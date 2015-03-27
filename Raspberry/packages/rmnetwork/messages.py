import sys
from packages.rmconfig import configtool
from constants import *

def appendBytes(data, append, LE=False):
    if LE:
        for b in reversed(append):
            data.append(int(b))
    else:
        for b in append:
            data.append(int(b))
    return data

def appendInt(data, num, LE=True):
    sizeBytes = [hex(num >> i & 0xff) for i in (24,16,8,0)]
    sizeBytes = [int(num >> i & 0xff) for i in (24,16,8,0)]
    return appendBytes(data, sizeBytes, LE)

def appendShort(data, num, LE=True):
    sizeBytes = [int(num >> i & 0xff) for i in (8,0)]
    return appendBytes(data, sizeBytes, LE)

def appendString(data, str, sizeLE=True):
    strBytes = []
    try:
        strBytes = bytearray(str, 'utf8')
    except:
        strBytes = bytearray(str)
    data = appendInt(data, len(strBytes), sizeLE)
    return appendBytes(data, strBytes)


def appendArg(data, type, arg):
    if type == '-f':
        global flag
        flag = int(arg)
    elif type == '-w':
        appendShort(data, int(arg))
    elif type == '-s':
        appendString(data, arg)
    elif type == '-i':
        appendInt(data, int(arg,0))

def getConfigMessage():
    config = configtool.readConfig()
    configStr = str(config)
    print "Sending config: " + configStr
    confBytes = bytearray(configStr)

    data = bytearray()
    size = 10 + len(confBytes)
    appendInt(data, size)
    appendShort(data, CONFIG_REQUEST)
    appendInt(data, len(confBytes))
    appendBytes(data, confBytes)

    return data

def getGroupConfigMessage():
    config = configtool.readGroupConfig()
    configStr = str(config)
    confBytes = bytearray(configStr)

    data = bytearray()
    size = 10 + len(confBytes)
    appendInt(data, size)
    appendShort(data, GROUP_CONFIG_REQUEST)
    appendInt(data, len(confBytes))
    appendBytes(data, confBytes)

    return data


def getMessage(flag, args=None):
    # append all arguments given as cmd args to usgData
    usgData = bytearray()
    if args:
        # print args
        for i in range(0,len(args)):
            arg = args[i]
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
    return data


def getTcpFileMessage(files, basePath):
    numFiles = len(files)

    data = bytearray()
    data = appendInt(data, numFiles, False)
    for filename in files:
        filePath = basePath + '/' + filename

        f=open (filePath, "rb")
        data = appendString(data, str(filename), sizeLE=False)

        fileData = f.read()
        filesize = len(fileData)
        data = appendInt(data, filesize, False)
        data.extend(fileData)
        #data = appendBytes(data, fileData)
    msgData = bytearray()
    msgSize = len(data)
    msgData = appendInt(msgData, msgSize, False)
    msgData = appendBytes(msgData, data)
    return msgData
