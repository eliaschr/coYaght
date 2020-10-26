# DeepSeaRobotix - coYaght
# ========================
# In the *coYaght*  system there is an  Arduino Uno that takes  measurements and controls its
# motors. The Arduino  communicates with the  Raspberry Pi 3B+ using a serial  communications
# port. Through this port the system can  reprogram the Arduino's  firmware and command it to
# switch on/off the motors of the coYaght. At the same time, there are some sensors connected
# to it; a temperature sensor, a light sensor and a pressure sensor. Added to all these there
# is also a battery  operated Real Time Clock to keep tracking of the date/time.  The Arduino
# takes  measurements of all these sensors every second and  transmits them  through the same
# serial  communications port.  All the results are stored in a database (MySQL) installed in
# the Raspberry Pi
#
# The following python module defines a class to control the updating of the local database
# and also the retrieval of its contents.
#

# Basic SQL commands:
# ===================
#
# For table creation:
# CREATE TABLE `measurements` (
#    `id` bigint unsigned NOT NULL AUTO_INCREMENT,
#    `DateStamp` DATETIME NOT NULL,
#    `Temp` DECIMAL(5,2) NOT NULL,
#    `Press` DECIMAL(8,2) NOT NULL,
#    `Depth` DECIMAL(7,3) NOT NULL,
#    `Lux` DECIMAL(7,2) NOT NULL,
#    `Batt` DECIMAL(4,2) NOT NULL,
#    PRIMARY KEY (`id`),
#    UNIQUE KEY `DateStamp` (`DateStamp`))
#    ENGINE InnoDB DEFAULT CHARSET=utf8;
#
# For inserting data into the table:
# INSERT INTO `measurements`(`DateStamp`, `Temp`, `Press`, `Depth`, `Lux`, `Batt`)
#    VALUES ("2020-07-17 21:22:34", 34.2, 98.72, 0.015, 548.34, 10.95);
#
# For fetching values from the table:
# SELECT * FROM `measurements`;
#

#
# (C) 2020, The DeepSeaRobotix Team of 1st Junior High School of Gerakas
# Under the Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International
# (CC BY-NC-SA 4.0) license.
# For the full license document, please follow:
# https://creativecommons.org/licenses/by-nc-sa/4.0/legalcode
#
# Summary of the license:
# =======================
#
# * You are free to:
#   Share — copy and redistribute the material in any medium or format
#   Adapt — remix, transform, and build upon the material
# The licensor cannot revoke these freedoms as long as you follow the license terms.
# * Under the following terms:
#   Attribution   — You must  give  appropriate  credit,  provide a link to the  license, and
#                   indicate if changes were made.  You  may do so in any  reasonable manner,
#                   but not in any way that suggests the licensor endorses you or your use.
#   NonCommercial — You may not use the material for commercial purposes.
#   ShareAlike    — If you remix, transform, or build upon the  material, you must distribute
#                   your contributions under the same license as the original.
# * No additional restrictions — You may not apply legal terms or technological measures that
#   legally restrict others from doing anything the license permits.
# * Notices:
#   You do not have to  comply with the  license for  elements of the  material in the public
#   domain or where your use is permitted by an applicable exception or limitation.
#   No warranties are given.  The license may not give you all of the  permissions  necessary
#   for your intended use.  For example,  other rights such as publicity,  privacy,  or moral
#   rights may limit how you use the material.
#
# THE  SOFTWARE  IS  PROVIDED  "AS IS",  WITHOUT  WARRANTY OF ANY KIND,  EXPRESS  OR IMPLIED,
# INCLUDING BUT NOT LIMITED TO THE  WARRANTIES OF  MERCHANTABILITY,  FITNESS FOR A PARTICULAR
# PURPOSE AND  NONINFRINGEMENT.  IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE
# FOR ANY  CLAIM,  DAMAGES OR OTHER  LIABILITY,  WHETHER  IN AN  ACTION OF CONTRACT,  TORT OR
# OTHERWISE,  ARISING  FROM, OUT OF OR IN  CONNECTION  WITH THE  SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.
#

# Import the needed modules
import sys
import pymysql
import threading

# The class that represents the MySQL Database is ArduinoDB
class ArduinoDB():

	# Initialize the necessrary variables. Normally the password of the database should be
	# defines in a more secure way than plain text in a variable. But for the purpose of this
	# project we leave it that way
	def __init__(self):
		self.connectedflg = False				# Not connected, yet
		self.dbhost = "localhost"
		self.dbuser = "coyaght"
		self.passwd = "coYaght_Gerakas"
		self.dbname = "coYaght"
		self.db = None
		self.cur = None
		self.lastData = None
		self.cond = threading.Condition()		# Condition for synchronizing the threads when
												# there are new data stored in the database

	# First things first. The instance must get connected to the MySQL database and set the
	# autocommit flag. For some reason, while MySQL has set this flag automatically, when
	# connected through python it acts as if it is not. So, to be safe we set it here, again.
	def connect(self):
		if self.db == None:
			try:
				self.db = pymysql.connect(host=self.dbhost, #Host of the database
							user=self.dbuser,		#User to be used
							passwd=self.passwd,		#Password
							db=self.dbname)			#Database to be used
			except:
				self.db = None
				return -1
			try:
				self.cur = self.db.cursor()
				self.cur.execute("SET autocommit=1")
				self.cond = threading.Condition()
			except:
				return -2
		return 0

	# When the system needs to release this resource it must disconnect from the database.
	def disconnect(self):
		if self.db != None:
			try:
				self.db.close()
				self.db = None
				self.cur = None
			except:
				self.db = None
				self.cur = None
				return -1;
		return 0;

	# Return the connection status of the instance
	def isconnected(self):
		return (self.cur != None)

	# Insert one row of data into 'measurements' table in the MySQL database
	def insert(self, indata):
		if self.db == None:
			return -1
		query = "INSERT INTO `measurements`(" + \
			"`DateStamp`, `Temp`,  `Press`, `Depth`, `Lux`,   `Batt`) VALUES (" + \
			"\"{0:s}\",   {1:.2f}, {2:.2f}, {3:.3f}, {4:.2f}, {5:.2f})".format(
				indata[0], indata[1], indata[2], indata[3], indata[4], indata[5])
		try:
			self.cur.execute(query)
			self.cond.acquire()
			self.lastData = indata
			self.cond.notify_all()
			self.cond.release()
		except:
			return -2
		return 0

	# Return the last inserted data. It does not perform a SELECT request to the database. It
	# only returns the local copy of the last stored data to avoid unnecessary transactions
	def fetchLastData(self):
		return self.lastData

	# Fetches a set of rows by performing a SELECT request to the database. The SELECT can
	# contain a Starting Date/Time, an Ending Date/Time, an optional LIMIT and an optional
	# OFFSET
	def fetchset(self, StartDate, EndDate, Limit = None, Offst = None):
		if self.db == None:
			return -1
		query = "SELECT * FROM `measurements`"
		if ((StartDate != None) or (EndDate != None)):
			query += " WHERE "
		if (StartDate != None):
			query += "DateStamp >= \"" + StartDate + "\""
		if ((StartDate != None) and (EndDate != None)):
			query += " AND "
		if (EndDate != None):
			query += "DateStamp <= \"" + EndDate + "\""
		if (Limit != None):
			query += " LIMIT " + str(Limit)
			if (Offst != None):
				query += " OFFSET " + str(Offst)
		try:
			self.cur.execute(query)
		except:
			return -2
		return self.cur.fetchall()

	# Returns the last rows of data stored in the database
	def fetchlast(self, Limit):
		if self.db == None:
			return -1
		query = "(SELECT * FROM `measurements` ORDER BY `id` DESC LIMIT " + str(Limit) + \
			") ORDER BY `id` ASC"
		try:
			self.cur.execute(query)
		except:
			return -2
		return self.cur.fetchall()

