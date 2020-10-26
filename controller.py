# DeepSeaRobotix - coYaght
# ========================
# In the *coYaght*  system there is an  Arduino Uno that takes  measurements and controls its
# motors. The Arduino  communicates with the  Raspberry Pi 3B+ using a serial  communications
# port. Through this port the system can  reprogram the Arduino's  firmware and command it to
# switch on/off the motors of the coYaght. At the same time, there are some sensors connected
# to it; a temperature sensor, a light sensor and a pressure sensor. Added to all these there
# is also a battery  operated Real Time Clock to keep tracking of the date/time.  The Arduino
# takes  measurements of all these sensors every second and  transmits them  through the same
# serial communications port, when instructed to do so.
# In order to be able to control the whole system and navigate it in the sea water and on its
# surface, there must be a user interface.  The idea is to have an HTML user interface, so an
# HTTP server is needed.  The following  program is a simple  server  based on a tutorial for
# live streaming its camera through web.  By expanding its  capabilities and tide it with the
# serial module of the  Arduino and the module for the database  connection, we can create an
# appropriate user interface.
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


# Web streaming server for coYaght
# Source code from the official PiCamera package
# http://picamera.readthedocs.io/en/latest/recipes2.html#web-streaming

# Import the needed modules
import os
import sys
import shutil
import io

# When the code runs as a *systemd service*,  the path is not the same as  when it is under a
# user's control in bash. So, we need to append a part of the path for the system to find the
# serial module installed in the user's directories.
if('/home/pi/.local/lib/python3.7/site-packages' not in sys.path):
	sys.path.append('/home/pi/.local/lib/python3.7/site-packages')

# Uncomment the following line to observe the final python3 path in systemd journal:
# sys.stderr.write("\n".join(sys.path))

# Now we can import the rest of the needed modules
import picamera
import logging
import socketserver
from threading import Condition
from http import server
import database
import serial_arduino as serino
import time


# A StreamingOutput class follows.  An instance of this class  holds the frames of the camera
# in order to send them through the network. The class provides a "frame" variable that holds
# the  frame to be sent when ready,  an  incoming "buffer"  the camera  stores its data and a
# "condition"" that synchronizes the consumer thread to fetch the frames when ready.
class StreamingOutput(object):
	def __init__(self):
		self.frame = None
		self.buffer = io.BytesIO()
		self.condition = Condition()

	def write(self, buf):
		if buf.startswith(b'\xff\xd8'):
			# New frame, copy the existing buffer's content and notify all
			# clients it's available
			self.buffer.truncate()
			with self.condition:
				self.frame = self.buffer.getvalue()
				self.condition.notify_all()
			self.buffer.seek(0)
		return self.buffer.write(buf)


# A StreamingHandler class to handle the incoming HTTP requests,  both of GET and POST types.
# This class is a child of the BaseHTTPRequestHandler, that the server needs.  For every HTTP
# request that  comes through  the network,  the server  creates an instance of this class to
# serve it.  In that way, the server can answer to many consecutive requests without problem.
# There are some access control lists (ACLs) applied,  to increase security  and stability of
# the system.
class StreamingHandler(server.BaseHTTPRequestHandler):
	# Access Control List for GET requests
	GetACList = [
		"/index.html",
		"/images/favicon.ico",
		"/images/logo.png",
		"/images/coYaght_top.png",
		"/images/coYaght_side.png",
		"/images/btn-up.png",
		"/images/btn-dn.png",
		"/images/btn-tfl.png",
		"/images/btn-tfr.png",
		"/images/btn-tbl.png",
		"/images/btn-tbr.png",
		"/images/btn-rcw.png",
		"/images/btn-rccw.png",
		"/images/btn-play.png",
		"/images/btn-stop.png",
		"/images/btn-pause.png",
		"/scripts/main.js",
		"/scripts/loader.js",
		"/scripts/jsapi_compiled_corechart_module.js",
		"/scripts/jsapi_compiled_default_module.js",
		"/scripts/jsapi_compiled_graphics_module.js",
		"/scripts/jsapi_compiled_ui_module.js",
		"/styles/main.css",
		"/styles/tooltip.css",
		"/styles/util.css"
		]

	# The types of the files that will be returned to the client
	GetACLTypes = [
		"text/html",
		"image/x-icon",
		"image/png",
		"image/png",
		"image/png",
		"image/png",
		"image/png",
		"image/png",
		"image/png",
		"image/png",
		"image/png",
		"image/png",
		"image/png",
		"image/png",
		"application/javascript",
		"application/javascript",
		"application/javascript",
		"application/javascript",
		"application/javascript",
		"application/javascript",
		"text/css",
		"text/css",
		"text/css"
		]

	# Access Control List for POST requests
	PostACList = [
		"/hbtn-all",
		"/btn-fr",
		"/btn-bk",
		"/btn-rccw",
		"/btn-rcw",
		"/hbtn-rlstp",
		"/btn-tfl",
		"/btn-tbr",
		"/hbtn-rstp",
		"/btn-tfr",
		"/btn-tbl",
		"/hbtn-lstp",
		"/btn-up",
		"/btn-dn",
		"/hbtn-vstp"
		]

	# Commands to be sent to Arduino's Serial Module, when there is the need to stop a motor
	PostCMDsOff = [
		0,
		5,
		5,
		5,
		5,
		5,
		8,
		8,
		8,
		11,
		11,
		11,
		14,
		14,
		14
		]
	
	# The path under which the web files are stored. All the requests are for files under
	# this path
	ROOTPATH = "/home/pi/coYaght/web"

	# GET requests handling
	def do_GET(self):
		# '/' redirects to index.html
		if self.path == '/':
			self.send_response(301)
			self.send_header('Location', '/index.html')
			self.end_headers()
		# Whatever is in the ACL for GET request is checked here and the file requested is
		# returned to the client
		elif self.path in self.GetACList:
			f = open(self.ROOTPATH + self.path, "rb")
			fs = os.fstat(f.fileno())
			
			self.send_response(200)
			self.send_header('Content-Type', self.GetACLTypes[self.GetACList.index(
				self.path)])
			self.send_header('Content-Length', str(fs[6]))
			self.end_headers()
			shutil.copyfileobj(f, self.wfile)
			f.close()
		# The "stream.jpg" requests a frame when the video is considered paused. The 't'
		# parameter is used to bypass the caching mechanism of the browser, so the real last
		# frame is requested.
		elif self.path.startswith('/stream.jpg?t='):
			try:
				with output.condition:
					output.condition.wait()
					frame = output.frame
				self.send_response(200)
				self.send_header('Age', 0)
				self.send_header('Cache-Control', 'no-cache, private')
				self.send_header('Pragma', 'no-cache')
				self.send_header('Content-Type', 'image/jpeg')
				self.send_header('Content-Length', len(frame))
				self.end_headers()
				self.wfile.write(frame)
				self.server.videoStat = False;
			except Exception as e:
				self.send_error(404)
				self.end_headers()
		# The "stream.mjpg" requests the stream from the camera, as mjpeg type. Again, in
		# order for the user to be able to pause and restart the video in his/her browser,
		# the 't' parameter is used. In that way the browser sends the new request again when
		# the video is unpaused.
		elif self.path.startswith('/stream.mjpg?t='):
			self.server.videoStat = True
			self.send_response(200)
			self.send_header('Age', 0)
			self.send_header('Cache-Control', 'no-cache, private')
			self.send_header('Pragma', 'no-cache')
			self.send_header('Content-Type', 'multipart/x-mixed-replace; boundary=FRAME')
			self.end_headers()
			try:
				while self.server.videoStat:
					with output.condition:
						output.condition.wait()
						frame = output.frame
					if(self.server.videoStat):
						self.wfile.write(b'--FRAME\r\n')
						self.send_header('Content-Type', 'image/jpeg')
						self.send_header('Content-Length', len(frame))
						self.end_headers()
						self.wfile.write(frame)
						self.wfile.write(b'\r\n')
			except Exception as e:
				logging.warning(
					'Removed streaming client %s: %s',
					self.client_address, str(e))
		else:
			self.send_error(404)
			self.end_headers()

	# POST requests handling
	def do_POST(self):
		# When the service is started, a connection to the serial port of the Arduino is made.
		# This takes some time. During that  time the Arduino cannot accept commands. So, the
		# client has to wait until the serial connection is established.
		if self.path == '/waitInit':
			content = '{"status":"Connected"}'
			self.send_response(200)
			self.send_header('Content-Type', 'application/json')
			self.send_header('Content-Length', len(content))
			self.end_headers()
			self.server.commport.waitInit()
			self.wfile.write(content.encode('utf-8'))
		# The Arduino hardware contains a Real Time Clock module. Using getRTC POST request,
		# the client can receive the time stored in it. The RTC module is battery backed-up,
		# so it keeps counting the time even when the whole system is off.
		# The return of the request is a JSON answer that contains the Arduino RTC time. This
		# is the time value used on the database INSERT requests.
		elif self.path == '/getRTC':
			self.send_response(200)
			tt = self.server.commport.getRTC()
			jstime = '{"year":' + str(tt.tm_year) + ','
			jstime += '"mon":' + str(tt.tm_mon) + ','
			jstime += '"mday":' + str(tt.tm_mday) + ','
			jstime += '"hour":' + str(tt.tm_hour) + ','
			jstime += '"min":' + str(tt.tm_min) + ','
			jstime += '"sec":' + str(tt.tm_sec) + ','
			jstime += '"wday":' + str(tt.tm_wday) + ','
			jstime += '"epoch":' + str(time.mktime(tt)) + '}'
			self.send_header('Content-Type', 'application/json')
			self.send_header('Content-Length', len(jstime))
			self.end_headers()
			self.wfile.write(jstime.encode('utf-8'))
		# When the 'btn-dst' POST request is issued, the Arduino is commanded to start
		# fetching data from the sensors and store them in the local database. The Arduino
		# command is send only of there was no similar command earlier issued.
		# The answer to that request is a JSON object containing the last information stored
		# in the database. Ot uses the condition from the database object to be notified when
		# new data are ready.
		elif self.path == '/btn-dst':
			self.send_response(200)
			self.server.commport.start_data()
#			self.server.dataStat = True
			try:
				with self.server.commport.db.cond:
					self.server.commport.db.cond.wait()
					indata = self.server.commport.db.fetchLastData()
					frame = '{"datestamp":"' + indata[0] + '",'
					frame += '"temp":' + str(indata[1]) + ','
					frame += '"pressure":' + str(indata[2]) + ','
					frame += '"depth":' + str(indata[3]) + ','
					frame += '"lux":' + str(indata[4]) + ','
					frame += '"battery":' + str(indata[5]) + '}'
#				if(self.server.dataStat):
					self.send_header('Content-Type', 'application/json')
					self.send_header('Content-Length', len(frame))
					self.end_headers()
					self.wfile.write(frame.encode('utf-8'))
			except Exception as e:
				logging.warning(
					'Removed streaming data client %s: %s',
					self.client_address, str(e))
		# The 'btn-dsp' POST request is used to stop the Arduino sending data of the sensors
		# to the database.
		elif self.path == '/btn-dsp':
			self.send_response(200)
			self.server.commport.stop_data()
#			self.server.dataStat = False
			self.send_header('Content-Type', 'plain/text')
			self.send_header('Content-Length', 0)
			self.end_headers()
		# The 'btn-vst' POST request starts the video streaming from the camera. Normally
		# this request is not used, as a 'stream.mjpg?t=...' GET request does the same and
		# also streams the data to the client
		elif self.path == '/btn-vst':
			self.server.videoStat = True
			self.send_response(200)
			self.send_header('Content-Type', 'plain/text')
			self.send_header('Content-Length', 0)
			self.end_headers()
		# The 'btn-vsp' POST request stops the video streaming from the camera. Normally
		# this request is not used, as a 'stream.jpg?t=...' GET request does the same and
		# also sends the last data frame to the client as a jpg image
		elif self.path == '/btn-vsp':
			self.server.videoStat = False
			self.send_response(200)
			self.send_header('Content-Type', 'plain/text')
			self.send_header('Content-Length', 0)
			self.end_headers()
		# Last but not least there is an Access Control List for the POST requests to handle
		# the starting/stopping of the motors
		elif self.path in self.PostACList:
			self.send_response(200)
			din = self.rfile.read(int(self.headers['Content-Length'])).decode()
			content = "Error"
			if din == "on":
				content = "On -> OK"
				self.server.commport.movecmd(self.PostACList.index(self.path))
			elif din == "off":
				content = "Off -> OK"
				self.server.commport.movecmd(self.PostCMDsOff[
					self.PostACList.index(self.path)])
			self.send_header('Content-Type', 'plain/text')
			self.send_header('Content-Length', len(content))
			self.end_headers()
			self.wfile.write(content.encode('latin-1'))
		else:
			self.send_error(404)
			self.end_headers()


# A StreamingServer class is the basic server class. Its inherits from HTTPServer class to do
# the serving job. Added to that is the keepinf of the video state and the associate serial
# port to the Arduino hardware module.
class StreamingServer(socketserver.ThreadingMixIn, server.HTTPServer):
	allow_reuse_address = True
	daemon_threads = True
	videoStat = True
#	dataStat = False

	def __init__(self, server_address, RequestHandlerClass, comm_port, bind_and_activate=True):
		super(StreamingServer, self).__init__(server_address, RequestHandlerClass,
			bind_and_activate)
		self.commport = comm_port


# MAIN PROGRAM:
#=============================================================================================

# Instantiate a connection to the database that holds the sensor data
mdb = database.ArduinoDB()
mdb.connect()

# Instantiate a connection to the Arduino serial port
comm = serino.SerProto('/dev/ttyACM0', mdb)
comm.connect()
#comm.waitInit()

# Start the camera fetching video and the instantiate the server
with picamera.PiCamera(resolution='640x480', framerate=24) as camera:
	output = StreamingOutput()
	#Uncomment the next line to change your Pi's Camera rotation (in degrees)
	#camera.rotation = 90
	camera.start_recording(output, format='mjpeg')
	try:
		address = ('', 80)
		srv = StreamingServer(address, StreamingHandler, comm)
		srv.serve_forever()
	finally:
		camera.stop_recording()
