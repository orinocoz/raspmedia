# -*- coding: utf-8 -*-
import sys, os, re
from constants import *

def appendBytes(data, append, LE=False):
	if LE:
		for b in reversed(append):
			data.append(b)
	else:
		for b in append:
			data.append(b)
	return data

def appendInt(data, num, LE=True):
	sizeBytes = [hex(num >> i & 0xff) for i in (24,16,8,0)]
	sizeBytes = [int(num >> i & 0xff) for i in (24,16,8,0)]
	return appendBytes(data, sizeBytes, LE)

def appendShort(data, num, LE=True):
	sizeBytes = [int(num >> i & 0xff) for i in (8,0)]
	return appendBytes(data, sizeBytes, LE)

def appendString(data, str, sizeLE=True):
	strByte = []
	try:
		strBytes = bytearray(str, 'utf-8')
	except:
		strBytes = bytearray(str)
	data = appendInt(data, len(strBytes), sizeLE)
	return appendBytes(data, strBytes)


def appendArg(data, type, arg):
	if type == '-f':
		# print "Saving FLAG"
		global flag
		flag = int(arg)
	elif type == '-w':
		# print "Appending SHORT"
		appendShort(data, int(arg))
	elif type == '-s':
		# print "Appending STRING"
		appendString(data, arg)
	elif type == '-i':
		# print "Appending INT"
		appendInt(data, int(arg))

def getConfigUpdateMessage(key, value):
	data = bytearray()
	usgData = bytearray()

	appendString(usgData, str(key))
	# print "KEY APPENDED!"
	if isinstance(value, (int)):
		# print "New config value is appended as INT!"
		appendInt(usgData, value)
	else:
		appendString(usgData, value)

	size = 6 + len(usgData)
	appendInt(data, size)
	appendShort(data, CONFIG_UPDATE)
	appendBytes(data, usgData)

	# print "Config message size: ", size
	return data

def getMessage(flag, args=None):
	# append all arguments given as cmd args to usgData
	usgData = None
	if args:
		usgData = bytearray()
		# print args
		for i in range(0,len(args)):
			arg = args[i]
			# print "Current arg: ", arg
			if arg.startswith('-'):
				if i < len(args) - 1:
					appendArg(usgData, arg, args[i+1])

	# combine msg size and usgData in final message to send in data
	data = bytearray()
	size = 6
	if usgData:
		size += len(usgData)
	appendInt(data, size)
	appendShort(data, flag)
	if usgData:
		appendBytes(data, usgData)

	# print "Message size: ", size
	return data

def getWifiConfigMessage(arg1, arg2):
	usgData = bytearray()
	appendShort(usgData, arg1["AUTHTYPE"])
	appendString(usgData, arg1["SSID"])
	appendString(usgData, arg2)

	data = bytearray()
	size = 6 + len(usgData)
	appendInt(data, size)
	appendShort(data, WIFI_CONFIG)
	appendBytes(data, usgData)

	# print "WifiConfig size: ", size
	return data

def getTcpFileMessage(files, basePath):
	numFiles = len(files)

	data = bytearray()
	data = appendInt(data, numFiles, False)
	thumbData = bytearray()
	for filename in files:
		filePath = os.path.join(basePath, filename)
		#filePath = basePath + '/' + filename
		if filename.endswith((SUPPORTED_IMAGE_EXTENSIONS)):
			data = appendInt(data, FILE_TYPE_IMAGE)
		else:
			data = appendInt(data, FILE_TYPE_VIDEO)
		f=open (unicode(filePath), "rb")
		#print "Appending filename %s with size %d" % (filename, len(bytearray(filename)))
		filename = makeStringPlayerSafe(filename)
		data = appendString(data, filename, sizeLE=False)

		fileData = f.read()
		filesize = len(fileData)
		data = appendInt(data, filesize, False)
		data = appendBytes(data, fileData)
		f.close()

	msgData = bytearray()
	msgSize = len(data)
	msgData = appendInt(msgData, msgSize, False)
	msgData = appendBytes(msgData, data)
	return msgData

def makeStringPlayerSafe(string):
	# replace whitespaces due to compatibility with omxplayer
	string = re.sub('[ ]', '_', string)
	# replace special characters
	string = re.sub(u'[ö]', 'oe', string)
	string = re.sub(u'[ä]', 'ae', string);
	string = re.sub(u'[ü]', 'ue', string);
	string = re.sub(u'[!@#$%&§+*]', '', string);
	return string