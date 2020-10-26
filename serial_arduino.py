# DeepSeaRobotix - coYaght
# ========================
# In the *coYaght*  system there is an  Arduino Uno that takes  measurements and controls its
# motors. The Arduino  communicates with the  Raspberry Pi 3B+ using a serial  communications
# port. Through this port the system can  reprogram the Arduino's  firmware and command it to
# switch on/off the motors of the coYaght. At the same time, there are some sensors connected
# to it; a temperature sensor, a light sensor and a pressure sensor. Added to all these there
# is also a battery  operated Real Time Clock to keep tracking of the date/time.  The Arduino
# takes  measurements of all these sensors every second and  transmits them  through the same
# serial communications port.
#
# The following python module defines a class to control all the serial communications to the
# Arduino Uno, needed for the proper functionality of the whole system through a web page.
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

# Import the necessary modules
import sys
import queue
import serial
import serial.threaded
import threading
import time

# The SerTrans class is the one that performs the transactions of the serial port. It is a
# child of LineReader to help receiving data from the serial port using independent thread,
# as the serial port works asynchronously from the rest of the system. It uses a Queue object
# to pass data to other threads as a FIFO. The queue can be specified during initialization
# or later using a call to setqueue method.
# The handle_line method is inherited from the LineReader class and just pushes the received
# data to the queue. If there is no queue set, the received serial data are gone to the bit
# oblivion :). There is also the write_line method that sends data to the serial stream.
class SerTrans(serial.threaded.LineReader):

	TERMINATOR = b'\r\n'
	ENCODING = 'ascii'

	def __init__(self, qpass = None):
		super(SerTrans, self).__init__()
		self.q = qpass


	def setqueue(self, qpass):
		self.q = qpass


	def handle_line(self, inline):
		if self.q != None:
			self.q.put(inline)


	def write_line(self, text):
		self.transport.write(text + self.TERMINATOR.decode(self.ENCODING))


# The SerThread class is a child of the ReaderThread one. The only difference is that the
# SerThread adds the usage of a Queue to be passed to the SerTrans instance created. All the
# rest are the same.
class SerThread(serial.threaded.ReaderThread):

	def __init__(self, serial_instance, protocol_factory, trans_queue):
		super(SerThread, self).__init__(serial_instance, protocol_factory)
		self.serq = trans_queue


	def run(self):
		if not hasattr(self.serial, 'cancel_read'):
			self.serial.timeout = 1
		self.protocol = self.protocol_factory(self.serq)
		try:
			self.protocol.connection_made(self)
		except Exception as e:
			self.alive = False
			self.protocol.connection_lost(e)
			self._connection_made.set()
			return
		error = None
		self._connection_made.set()
		while self.alive and self.serial.is_open:
			try:
				data = self.serial.read(self.serial.in_waiting or 1)
			except serial.SerialException as e:
				error = e
				break
			else:
				if data:
					try:
						self.protocol.data_received(data)
					except Exception as e:
						error = e
						break
		self.alive = False
		self.protocol.connection_lost(error)
		self.protocol = None


# The SerProto class defines the protocol to the Arduino using the serial port. An instance of
# this class represents one serial port that communicates data with the Arduino hardware. It
# also creates the necessary instances of the other two classes defined earlier in this file
# to be able to send and receive serial data asynchronously.
class SerProto():

	TERMSTRING = "TERMINATE"
	TERMINATOR = b"\r\n"
	ENCODING = 'utf-8'
	
	# Commands the Arduino accepts
	mComms = [
		"ms",									#All motors stop
		"mmf",									#Move forward
		"mmb",									#Move backwards
		"mml",									#Rotate left
		"mmr",									#Rotate right
		"mms",									#Stop both left and right motors
		"mrf",									#Turn right forward
		"mrb",									#Turn right backwards
		"mrs",									#Stop right motor
		"mlf",									#Turn left forward
		"mlb",									#Turn left backwards
		"mls",									#Stop left motor
		"mdu",									#Ascent towards surface
		"mdd",									#Dive
		"mds"									#Stop vertical motor
		]
	
	# Initialization of the instance. Here are the default settings for the serial port. The
	# input provides a port_id that is the serial port to be used and a Database object that
	# is used to store the incoming data of the sensors.
	def __init__(self, port_id, DBobj):
		self.port_id = port_id					#Port file of Arduino
		self.baudrate = 9600					#The baud rate is 9600
		self.bytesize = serial.EIGHTBITS		#8N1 communication type
		self.parity = serial.PARITY_NONE
		self.stopbits = serial.STOPBITS_ONE
		self.rtscts = False						#RTS/CTS are not used
		self.xonxoff = False					#XOn/XOff characters are not used
		self.ser = None							#No serial port object used yet
		self.status = 0							#Currently disconnected
		self.initstate = 0						#Initializing State
		self.initlock = threading.Lock()		#Lock for async init waiting
		self.initlock.acquire()
		self.serq = None						#A queue as a connector between DB and Serial
		self.serqThread = None					#The thread of the q getter
		self.db = DBobj							#The database handler object
		self.RdThread = None					#The ReaderThread
		self.dateflag = False					#Asked arduino for its RTC time, flag
		self.getdateevent = threading.Event()	#Event for expecting date from Arduino
		self.cmddatelock = threading.Lock()		#Lock for issuing a "get date" request
		self.datestr = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
		self.dataStat = False					#Status of data fetching from Arduino

	# The first thing needed is to connect to the serial port. This is handled by the
	# connect method.
	def connect(self):
		if self.ser == None:
			self.ser = serial.serial_for_url(self.port_id, do_not_open = True)
			self.ser.baudrate = self.baudrate
			self.ser.bytesize = self.bytesize
			self.ser.parity = self.parity
			self.ser.stopbits = self.stopbits
			self.ser.rtscts = self.rtscts
			self.ser.xonxoff = self.xonxoff
			return self.open()
		return 0

	# Part of the 'connect' process is to open the port and instantiate the necessary threads
	# for the system to be able to exchange data through the serial port
	def open(self):
		if self.ser == None:
			raise serial.SerialException('Serialino/open: Not connected to any serial port')
			return -3
		if self.ser.is_open:
			sys.stderr.write('Attempt to open an already opened serial port {}\n'.format(
				self.ser.name))
			#return -1
		if self.status == 1:
			return 0
		self.status = 0
		#self.initstate = 0
		if not self.ser.is_open:
			try:
				self.ser.open()
			except serial.SerialException as e:
				sys.stderr.write('Could not open Arduino serial port {}: {}\n'.format(
					self.ser.name, e))
				return -2
		if self.RdThread == None:
			self.serq = queue.Queue()
			self.serqThread = threading.Thread(target=self.incoming, daemon = True)
			self.serqThread.start()
			self.RdThread = SerThread(self.ser, SerTrans, self.serq)
			self.RdThread.start()
			self.RdThread.connect()
		self.status = 1
		return 0

	# When the serial port is not needed any more we have to close and disconnect from it.
	# This is necessary to free the serial port and make it available to some other program.
	# The 'close' method just kills the threads created by 'open'
	def close(self):
		self.RdThread.close()
		self.RdThread = None
		self.serq.put(self.TERMSTRING)
		self.serqThread.join()

	# Disconnect is used to handle the disconnection from the serial port. As this is happened
	# when the associated thread is terminated, only some cleanup is performed here.
	def disconnect(self):
		if self.ser == None:
			sys.stderr.write("Serialin/disconnect: Not connected to any serial port")
			return 0
		if not self.ser.is_open:
			sys.stderr.write('Attempt to close a non opened serial port {}\n'.format(
				self.serial.name))
			return 0
		if self.status == 0:
			return 0
		#self.ser.close()					#Closed earlier by the thread
		self.status = 0
		self.initstate = 0
		self.initlock.acquire()
		return 0

	# The following method sends a command to the arduino hardware to make it start taking
	# measurements from the sensors. The command is 'S1'. This command is sent only when there
	# are no measurements done by the Arduino. Otherwise, it is ignored.
	def start_data(self):
		if not self.dataStat:
			if self.initstate == 0:
				sys.stderr.write('Arduino serial port {} is not ready. Could not Start\n'.format(
					self.serial.name))
				return -1
			try:
				self.write_line("S1")
			except:
				sys.stderr.write('Could not send data to Arduino port [S1]\n')
				return -2
			self.dataStat = True;
		return 0

	# 'stop_data' method sends the appropriate command, 'S0' to the arduino to make it stop
	# taking measurements from the sensors. The arduino must be previously started with
	# 'start_data', otherwise this command is ignored
	def stop_data(self):
		if self.dataStat:
			if self.initstate == 0:
				sys.stderr.write('Arduino serial port {} is not ready. Could not Stop\n'.format(
					self.serial.name))
				return -1
			try:
				self.write_line("S0")
			except:
				sys.stderr.write('Could not send data to Arduino port [S0]\n')
				return -2
			self.dataStat = False
		return 0

	# The Arduino hardware contains a battery backed-up real time clock. This counts the time
	# even if the system is not powered up by an external supply. In order to fetch its stored
	# date/time value the 'getRTC' method must be called. It returns a time_struct containing
	# the date/time returned by the RTC
	def getRTC(self):
		if self.initstate == 0:
			sys.stderr.write('Arduino serial port {} is not ready. ' + \
				'Could not get time\n'.format(self.serial.name))
			return -1
		self.cmddatelock.acquire()
		self.write_line("D1")
		self.dateflag = True
		self.getdateevent.clear()
		self.cmddatelock.release()
		self.getdateevent.wait()
		return time.strptime(self.datestr, "%Y-%m-%d %H:%M:%S")

	# When there is the need to set a new Date/Time value to the RTC of the Arduino, the
	# 'setRTC' method is used. It takes a time_struct as an input and sends the appropriate
	# command through the serial port.
	def setRTC(self, indate):
		if self.initstate == 0:
			sys.stderr.write('Arduino serial port {} is not ready. Could not set time\n'\
				.format(self.ser.name))
			return -1
		self.write_line("T" + time.strftime("%d-%m-%y %H:%M:%S", indate))
		return 0

	# 'movecmd' method sends a move command. The accepted move commands are described in the
	# mComms[] table. The input parameter gives the index of the table that contains the
	# command to be sent.
	def movecmd(self, cmdin):
		if self.initstate == 0:
			sys.stderr.write('Arduino serial port {} is not ready. Could not Stop\n'.format(
				self.serial.name))
			return -1
		try:
			if ((cmdin >= 0) and (cmdin <= 14)):
				self.write_line(self.mComms[cmdin])
			else:
				return -3
		except:
			sys.stderr.write('Could not send data to Arduino port [' + self.mComms[cmdin] +
				']\n')
			return -2
		return 0

	# When the serial port is opened, the Arduino perform some initialization that takes some
	# seconds. During that time no command is accepted. By calling 'waitInit' method, we can
	# ensure that the system is properly initialized and can accept commands.
	def waitInit(self):
		self.initlock.acquire()					#Try to acquire the lock. It is released only
												# if the arduino subsystem is initialized.
		self.initlock.release()					#Release the lock again. No reason to keep it

	# Just another 'write_line' method to send data to the serial port
	def write_line(self, text):
		self.RdThread.write(text.encode(self.ENCODING) + self.TERMINATOR)

	# The following method becomes the queue handling thread. It receives data from the queue
	# when another thread pushes data into it and performs the necessary task asked by the
	# caller; reading the time or fetching measurements and store them in the database
	def incoming(self):
		runme = True
		while runme:
			inline = self.serq.get()
			self.serq.task_done()
			if self.initstate == 0:
				if inline == 'STATUS: Setup complete':
					self.initstate = 1
					self.initlock.release()			#Releasing the lock means the arduino is
													# initialized
			else:
				if inline == 'STATUS: Initializing':
					self.initstate = 0
					self.initlock.acquire()			#Acquiring the lock means the arduino is
													# not initialized and we have to wait
													# until it can accept any commands
				elif inline == self.TERMSTRING:
					runme = False					#Terminate this loop, thus terminating the
													# thread
				else:
					self.cmddatelock.acquire()		#Is there a D1 command on the way? Have to
													# wait until it is done
					if inline.startswith("Date="):	#Line with sensors measurements?
						inset = inline.split(", ")	#Split the parts of the string
						indat = []
						for i in inset:
							indat.append(i.split("=")[1])	#Keep only the data values
							try:
								indat[-1] = float(indat[-1])
							except:
								pass
						self.datestr = indat[0]		#Shape the date string
						self.db.insert(indat)		#Store the data into the database
					else:
						self.datestr = inline
					if self.dateflag:				#Does the system need to fetch the date?
						self.dateflag = False
						self.getdateevent.set()
					self.cmddatelock.release()		#Release the lock of 'D1' command
