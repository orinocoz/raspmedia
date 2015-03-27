import os, threading, socket, time
from constants import *
from packages.rmmedia import mediaplayer
from packages.rmconfig import configtool
from packages.rmnetwork import udplocalforwarder
import GroupManager


def interpret(msg_data, sender_ip=None):
    #print "Interpreting incoming data..."
    if str(msg_data).startswith("rm"):
        # string interpretation
        result = INTERPRETER_SUCCESS
        msg = None
        values = str(msg_data).split(":")
        cmd = values[1]
        if cmd == "state":
            val = values[2]
            # switch state
            mediaplayer.setState(int(val))
        elif cmd == "number":
            val = values[2]
            mediaplayer.setMediaFileNumber(int(val))
        elif cmd == "next":
            mediaplayer.nextFile()
        elif cmd == "prev":
            mediaplayer.prevFile()
        elif cmd == "config":
            # config must be sent as key/value pair
            if len(values) == 4:
                key = values[2]
                value = values[3]
                print "New Key/Value Pair:"
                print "KEY: ", key
                print "VALUE: ", value
                configtool.setConfigValue(key, value)
        elif cmd == "hdmi":
            val = values[2]
            os.system(os.getcwd()+"/scripts/rpi-hdmi.sh "+val)
        else:
            result = INTERPRETER_ERROR
            msg = "Unknown UDP string command"
    else:
        data = bytearray(msg_data)
        size, data = readInt(data)
        #print "Size: " + str(size)

        flag, data = readShort(data)
        result = flag;
        msg = None
        #print "Flag: " + str(flag)
        if flag == CONFIG_UPDATE:
            data = readConfigUpdate(data)
        elif flag == PLAYER_START:
            print 'UDP COMMAND Mediaplayer start...'
            mediaplayer.setState(1)
        elif flag == PLAYER_STOP:
            print 'UDP COMMAND Mediaplayer stop...'
            mediaplayer.setState(0)
        elif flag == PLAYER_PAUSE:
            mediaplayer.setState(3)
        elif flag == PLAYER_RESTART:
            print 'UDP COMMAND Mediaplayer restart...'
            mediaplayer.playerState = PLAYER_STOPPED
            mediaplayer.stop()
            time.sleep(2)
            mediaplayer.playerState = PLAYER_STARTED
            mediaplayer.play()
        elif flag == SERVER_REQUEST:
            data = None
            result = SERVER_REQUEST
        elif flag == FILELIST_REQUEST:
            result = FILELIST_REQUEST
        elif flag == FILELIST_RESPONSE:
            readFileList(data)
            result = FILELIST_REQUEST
        elif flag == CONFIG_REQUEST:
            result = CONFIG_REQUEST
        elif flag == DELETE_FILE:
            numFiles, data = readInt(data)
            files = []
            for i in range(numFiles):
                msg, data = readString(data)
                if msg:
                    files.append(msg)
            mediaplayer.deleteFiles(files)
        elif flag == DELETE_ALL_IMAGES:
            files = mediaplayer.getImageFilelist()
            mediaplayer.deleteFiles(files)
        elif flag == PLAYER_IDENTIFY:
            print 'Showing identify image...'
            mediaplayer.identifySelf()
        elif flag == PLAYER_IDENTIFY_DONE:
            print 'Identifying done...'
            mediaplayer.identifyDone()
        elif flag == PLAYER_REBOOT:
            os.system("sudo reboot")
        elif flag == PLAYER_UPDATE:
            if is_connected():
                os.system("/home/pi/raspmedia/Raspberry/scripts/update.sh")
            else:
                result = PLAYER_UPDATE_ERROR
                msg = "Player is not connected to the internet."
        elif flag == WIFI_CONFIG:
            setupWifi(data)
        ### GROUP AND ACTION MESSAGE FLAGS ###
        elif flag == GROUP_CONFIG_REQUEST:
            result = flag
        elif flag == GROUP_MEMBER_REQUEST:
            group, data = readString(data)
            GroupManager.MemberRequest(group, sender_ip)
        elif flag == GROUP_MEMBER_ACKNOWLEDGE:
            group, data = readString(data)
            byRequest , data = readInt(data)
            GroupManager.MemberAcknowledge(group, sender_ip, byRequest)
        elif flag == GROUP_CONFIG:
            result = flag
            readGroupConfig(data)
        elif flag == GROUP_DELETE:
            result = flag
            groupName, data = readString(data)
            if configtool.readGroupConfig()['group'] == groupName:
                configtool.resetGroupConfig()
                gConf = configtool.readGroupConfig()
                GroupManager.ReInitGroupManager(gConf)
        elif flag == GROUP_CONFIG_ADD_ACTION:
            result = flag
            msg, data = readString(data)
        elif flag == GROUP_CONFIG_ACTION_DELETE:
            result = flag
            msg, data = readString(data)
        elif flag == FILE_DATA_REQUEST:
            result = flag
        elif flag == PLAYER_START_FILENUMBER:
            print "UDP COMMAND Start Filenumber..."
            number, data = readInt(data)
            mediaplayer.startFileNumber(number)
        elif flag == DISK_INFO_REQUEST:
            result = flag
        elif flag == PLAYER_SET_FILENUMBER:
            result = flag
            mediaNumber, data = readInt(data)
            mediaplayer.setMediaFileNumber(mediaNumber)
        elif flag == PLAYER_CLEAR_FILENUMBER:
            result = flag
            mediaplayer.setMediaFileNumber(-1)
        else:
            result = INTERPRETER_ERROR
            msg = "Unknown command flag"

        #print "Remaining data: " + data.decode("utf-8")

    return result, msg

def readGroupConfig(data):
    name, data = readString(data)
    mInt, data = readInt(data)
    master = mInt == 1
    print "Updating Group Configuration:"
    print "Name: %s" % (name)
    print "Master: ", master
    configtool.setGroupConfigValue("group", name)
    configtool.setGroupConfigValue("group_master", mInt)
    gConf = configtool.readGroupConfig()
    GroupManager.ReInitGroupManager(gConf)

def setupWifi(data):
    auth, data = readShort(data)
    ssid, data = readString(data)
    key, data = readString(data)

    os.system("sudo mv /etc/network/interfaces /etc/network/interfaces.old")
    os.system("sudo touch /etc/network/interfaces")

    # echo the new content for the interfaces file
    file = "/etc/network/interfaces"
    __echoLine('auto lo',file)
    __echoLine('iface lo inet loopback',file)
    __echoLine('iface eth0 inet dhcp',file)

    if len(ssid) > 0 and (len(key) > 0 or auth == WIFI_AUTH_NONE):
        __echoLine('allow-hotplug wlan0',file)
        __echoLine('auto wlan0',file)
        __echoLine('iface wlan0 inet dhcp',file)
        if auth == WIFI_AUTH_WPA:
            __echoLine('    wpa-ssid "' + ssid + '"',file)
            __echoLine('    wpa-psk "' + key + '"',file)
        elif auth == WIFI_AUTH_WEP:
            __echoLine('    wireless-essid ' + ssid,file)
            __echoLine('    wireless-key ' + key,file)
        elif auth == WIFI_AUTH_NONE:
            __echoLine('    wireless-essid ' + ssid,file)


def __echoLine(line,dest):
    os.system("sudo echo '" + line + "' >> " + dest)


def readFileList(data):
    numFiles, data = readInt(data)
    files = []
    for i in range(numFiles):
        file, data = readString(data)
        if file:
            files.append(file)
    print "FILE LIST READ: ", files

def readConfigUpdate(data):
    #print "Current config: ", configtool.config
    #print "Processing config update message..."
    key, data = readString(data)
    value, data = readConfigValue(data, key)
    print "New Key/Value Pair:"
    print "KEY: ", key
    print "VALUE: ", value
    configtool.setConfigValue(key, value)
    if key == "blend_type":
        # pass blendType directly to qt viewer if currently running
        if mediaplayer.qtViewerActive():
            udplocalforwarder.forwardNewBlendType(CONFIG_UPDATE, value)
    return data

def readConfigValue(data, key):
    if key == 'image_interval' or key == 'image_blend_interval' or key == 'image_enabled' or key == 'video_enabled' or key == 'shuffle' or key == 'repeat' or key == 'autoplay':
        # integer config value
        value, data = readInt(data)
    else:
        # string config value
        value, data = readString(data)
    return value, data

def readInt(data):
    intBytes = data[:4]
    remainingData = data[4:]
    #num = (intBytes[0] << 24) + (intBytes[1] << 16) + (intBytes[2] << 8) + intBytes[3]
    # LE change
    num = (intBytes[3] << 24) + (intBytes[2] << 16) + (intBytes[1] << 8) + intBytes[0]
    return num, remainingData

def readShort(data):
    intBytes = data[:2]
    remainingData = data[2:]
    #num = (intBytes[0] << 8) + intBytes[1]
    # LE change
    num = (intBytes[1] << 8) + intBytes[0]
    return num, remainingData

def readString(data):
    size, data = readInt(data)
    strBytes = data[:size]
    remainingData = data[size:]
    inStr = str(strBytes)
    return inStr, remainingData

def is_connected():
  try:
    # see if we can resolve the host name -- tells us if there is
    # a DNS listening
    host = socket.gethostbyname('www.google.com')
    # connect to the host -- tells us if the host is actually
    # reachable
    s = socket.create_connection((host, 80), 2)
    return True
  except:
     pass
  return False
