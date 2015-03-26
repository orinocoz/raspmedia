import sys, threading, time
import socket, select

# global socket variable
sock = None

def forwardFlagCommand(cmdNum):
    msgData = bytearray()
    msgData = appendShort(msgData, cmdNum)
    __sendMessageToLocalhost(msgData)

def forwardValueCommand(cmdNum, value):
    msgData = bytearray()
    msgData = appendShort(msgData, cmdNum)
    msgData = appendShort(msgData, value)
    __sendMessageToLocalhost(msgData)

def __sendMessageToLocalhost(data):
    global sock
    host = "127.0.0.1"
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    port = 60606
    # if valid message data present --> send it
    if data:
        sock.sendto(data + "\n", (host, port))
    sock.close()

def appendShort(data, num, LE=True):
    sizeBytes = [int(num >> i & 0xff) for i in (8,0)]
    return appendBytes(data, sizeBytes, LE)

def appendInt(data, num, LE=True):
    sizeBytes = [hex(num >> i & 0xff) for i in (24,16,8,0)]
    sizeBytes = [int(num >> i & 0xff) for i in (24,16,8,0)]
    return appendBytes(data, sizeBytes, LE)

def appendBytes(data, append, LE=False):
    if LE:
        for b in reversed(append):
            data.append(int(b))
    else:
        for b in append:
            data.append(int(b))
    return data
