import serial
import time
import binascii
import struct
import io

units = "metric"
prompt = 0
pageData = ""

def readHandshake(connection):
	global prompt
	#read handshake
	version = ""
	#todo: better method for waiting for handshake
	while version != '0203':
		version = connection.read(2).encode('hex')
		serial = connection.read(2).encode('hex')
		ltime = connection.read(4).encode('hex')
		boot_count = connection.read(2).encode('hex')
		boot_time = connection.read(4).encode('hex')
		dive_count = connection.read(2).encode('hex')
		interval = connection.read(2).encode('hex')
		threshold = connection.read(2).encode('hex')
		endcount = connection.read(2).encode('hex')
		averaging = connection.read(2).encode('hex')
		crc = connection.read(2).encode('hex')
		prompt = int(connection.read(1).encode('hex'), 16)
		#print "version: %i" % int(struct.pack("<I", int(version, 16)).encode('hex')[:-4], 16)
		#print "serial: %i" % int(struct.pack("<I", int(serial, 16)).encode('hex')[:-4], 16)
		#print "time: %i" % long(struct.pack("<I", long(ltime, 16)).encode('hex'), 16) #possibly incorrect
		#print "boot_count: %i" % int(struct.pack("<I", int(boot_count, 16)).encode('hex')[:-4], 16)
		#print "boot_time: %i" % long(struct.pack("<I", long(boot_time, 16)).encode('hex'), 16) #possibly incorrect
		#print "dive_count: %i" % int(struct.pack("<I", int(dive_count, 16)).encode('hex')[:-4], 16)
		#print "interval: %i" % int(struct.pack("<I", int(interval, 16)).encode('hex')[:-4], 16)
		#print "threshold: %i" % int(struct.pack("<I", int(threshold, 16)).encode('hex')[:-4], 16)
		#print "endcount: %i" % int(struct.pack("<I", int(endcount, 16)).encode('hex')[:-4], 16)
		#print "averaging: %i" % int(struct.pack("<I", int(averaging, 16)).encode('hex')[:-4], 16)
		#print "crc: %i" % int(struct.pack("<I", int(crc, 16)).encode('hex')[:-4], 16)
		#print "prompt: %i" % prompt

def requestSense(connection):
	global prompt
	if prompt == 165:
		#least significant
		instruction = "\x40"
		#print "instruction %s" % instruction
		connection.write(instruction)
		prompt = int(connection.read(1).encode('hex'), 16)

	if prompt == 165:
		#most significant
		instruction = "\xB4"
		#print "instruction %s" % instruction
		connection.write(instruction)
		readSense(connection)
	else:
		print "no response from logger"
		time.sleep(0.25)


def readSense(connection):
	voltage = int(struct.pack("<I", int(connection.read(2).encode('hex'), 16)).encode('hex')[:-4], 16) / float(1000)
	print "voltage: %.3f V" % voltage
	#temp is 0.01 Kelvin
	if units == "metric":
		temperature = float(int(struct.pack("<I", int(connection.read(2).encode('hex'), 16)).encode('hex')[:-4], 16) / float(100)) - 273.15
		print "temperature: %.2f C" % temperature
	else:
		print "sorry no metric support"
	pressure = int(struct.pack("<I", int(connection.read(2).encode('hex'), 16)).encode('hex')[:-4], 16)
	print "pressure %i MBAR" % pressure
	crc = connection.read(2)

def requestData(connection):
	global prompt
	if prompt == 165:
		#least significant
		instruction = "\x20"
		#print "instruction %s" % instruction
		connection.write(instruction)
		prompt = int(connection.read(1).encode('hex'), 16)

	if prompt == 165:
		#most significant
		instruction = "\xB4"
		#print "instruction %s" % instruction
		connection.write(instruction)
		readData(connection)
	else:
		print "no response from logger"

def readPageData(pageData):
	pageData = pageData.encode('hex')
	sol = '0000'
	eol = 'ffff'
	lensol = len(sol)
	leneol = len(eol)
	line = ""
	print "reading data..."
	for c in pageData:
		line += c
		if line[-lenesol:] == eol:
			print "DATA READ..."

def readData(connection):
	global prompt, pageData
	pageNumber = connection.read(2).encode('hex')
	#hack for page 770
	if int(struct.pack("<I", int(pageNumber, 16)).encode('hex')[:-4], 16) == 770:
		readPageData(pageData)
		pageData = bytearray()
	else:
		print "Reading page: %i" % int(struct.pack("<I", int(pageNumber, 16)).encode('hex')[:-4], 16)
		#pageData += connection.read(512).encode('hex')
		pageData += connection.read(512)
		pageCrc = connection.read(2).encode('hex')
		prompt = int(connection.read(1).encode('hex'), 16)
		if prompt == 165:
			instruction = "\xA5"
			connection.write(instruction)
			readData(connection)
		else:
			readPageData(pageData.encode('hex'))
			return True

#serial port 0=COM1 etc
ser = serial.Serial(port=7,baudrate=115200, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, bytesize=serial.EIGHTBITS, timeout=100)
ser.xonxoff = False     #disable software flow control
ser.rtscts = False     #disable hardware (RTS/CTS) flow control
ser.dsrdtr = False

print "connected to: " + ser.name

readHandshake(ser)
requestSense(ser)
readHandshake(ser)
requestData(ser)
ser.close()