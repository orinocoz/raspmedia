#! /usr/bin/env python

import os, platform, threading, time, subprocess, re
from packages.rmutil import processtool
from packages.rmconfig import configtool
from constants import *
from pyomxplayer import OMXPlayer
import ImageIdentifier

playerState = PLAYER_STOPPED
cwd = os.getcwd()
mediaPath = cwd + '/media/'
mp_thread = None
qt_proc = None
identifyFlag = False
previousState = None
filenumber = None
blackout = False
videoPlaying = False

class MediaPlayer(threading.Thread):
    def __init__(self):
        global playerState
        self.mediaPath = os.getcwd() + '/media/'
        self.runevent = threading.Event()
        self.pauseevent = threading.Event()
        self.pauseevent.set()
        self.identify_event = threading.Event()
        playerState = PLAYER_STOPPED
        self.initImageAliases()
        threading.Thread.__init__(self, name="MediaPlayer_Thread")

    def initImageAliases(self):
        if not os.path.isfile(cwd + '/img_al1.jpg'):
            subprocess.call(["ln", "-s", "-f", cwd + '/raspblack.jpg', cwd + '/img_al1.jpg'])
        if not os.path.isfile(cwd + '/img_al2.jpg'):
            subprocess.call(["ln", "-s", "-f", cwd + '/img_al1.jpg', cwd + '/img_al2.jpg'])
        if not os.path.isfile(cwd + '/img_al3.jpg'):
            subprocess.call(["ln", "-s", "-f", cwd + '/img_al1.jpg', cwd + '/img_al3.jpg'])

    def run(self):
        global playerState, identifyFlag
        #print ":::::MEDIAPLAYER THREAD RUN METHOD STARTED:::::"
        self.reloadConfig()
        blendInterval = str(self.config['image_blend_interval'])
        # call initial fbi command
        imgCmdList = ["sudo","fbi","-noverbose", "-cachemem", "0", "-t", "1", "-blend", blendInterval, "-T","2", cwd + '/img_al1.jpg', cwd + '/img_al2.jpg', cwd + '/img_al3.jpg']
        subprocess.call(imgCmdList)
        # show player startup image for 3 seconds (+ loading time)
        self.showRaspMediaImage()
        time.sleep(5)
        self.blackout()
        # enter media player thread loop
        while True:
            # wait until the player flag is set to STARTED
            #while playerState == PLAYER_STOPPED:
            #    time.sleep(0.5)
            self.runevent.wait()
            # remove raspmedia image process
            # processtool.killProcesses('fbi')

            if identifyFlag:
                self.showIdentifyImage()
                self.identify_event.wait()
                if playerState == PLAYER_STOPPED:
                    self.blackout()
            else:
                #reload config and process media files
                self.reloadConfig()
                playerState = PLAYER_STARTED
                print "BLACKOUT: ",blackout
                if blackout:
                    print "Blackout screen..."
                    self.blackout()
                else:
                    self.processMediaFiles()
                time.sleep(0.5)
                self.blackout()

    def showRaspMediaImage(self):
        global cwd
        #cmdList = ['sudo','fbi','-noverbose','-T','2', '-a', cwd + '/raspmedia.jpg']
        #subprocess.call(cmdList)
        # link to raspmedia background image
        subprocess.call(["ln", "-s", "-f", cwd + '/raspmedia.jpg', cwd + '/img_al1.jpg'])

    def showIdentifyImage(self):
        global cwd
        path = cwd
        if os.path.isfile(cwd + '/raspidentified.jpg'):
            path += '/raspidentified.jpg'
        else:
            path += '/raspidentify.jpg'
        #cmdList = ['sudo','fbi','-noverbose','-T','2', '-a', path]
        #subprocess.call(cmdList)
        # link to identify image
        subprocess.call(["ln", "-s", "-f", path, cwd + '/img_al1.jpg'])

    def setMediaPath(self, mediaPath):
        self.mediaPath = mediaPath

    def processImagesOnce(self):
        global playerState
        #imgInterval = str(self.config['image_interval'])
        imgInterval = self.config["image_interval"]-1
        blendInterval = str(self.config['image_blend_interval'])
        #imgCmdList = ["sudo","fbi","-noverbose", "--once", "-readahead", "-t", imgInterval, '-a', "-blend", blendInterval, "-T","2"]
        #imgCmdList = ["sudo","fbi","-noverbose", "-cachemem", "0", "-t", "1", '-a', "-blend", blendInterval, "-T","2", cwd + '/img_al1.jpg', cwd + '/img_al2.jpg', cwd + '/img_al3.jpg']
        files = sorted(self.allImages())
        
        # loop through image files once
        for file in files:
            # link new image
            if self.runevent.is_set():
                # image interval passed, player did not change into stopped state --> link next image
                subprocess.call(["ln", "-s", "-f", os.path.join(self.mediaPath, file), cwd + '/img_al1.jpg'])
                time.sleep(0.7)
            # wait image interval
            interval = 0
            while self.runevent.is_set() and interval < imgInterval:
                time.sleep(1)
                interval += 1
                self.pauseevent.wait()


    def fbiImageLoop(self):
        global playerState
        imgInterval = self.config['image_interval']
        blendInterval = str(self.config['image_blend_interval'])
        # imgCmdList = ["sudo","fbi","-noverbose", "-readahead", "-t", imgInterval, '-a', "-blend", blendInterval, "-T","2"]
        #imgCmdList = ["sudo","fbi","-noverbose", "-cachemem", "0", "-t", "1", '-a', "-blend", blendInterval, "-T","2", cwd + '/img_al1.jpg', cwd + '/img_al2.jpg', cwd + '/img_al3.jpg']
        files = sorted(self.allImages())
        
        # loop over images as long as runevent is set
        while self.runevent.is_set():
            for file in files:
                if self.runevent.is_set():
                    # image interval passed, player did not change into stopped state --> link next image
                    subprocess.call(["ln", "-s", "-f", os.path.join(self.mediaPath, file), cwd + '/img_al1.jpg'])
                    time.sleep(0.7)
                # wait image interval
                interval = 0
                while self.runevent.is_set() and interval < imgInterval:
                    time.sleep(1)
                    interval += 1
                    self.pauseevent.wait()

    def processImagesWithQtViewer(self):
        global playerState
        global qt_proc
        imgInterval = str(self.config['image_interval'])
        blendInterval = str(self.config['image_blend_interval'])
        loops = 0
        if self.config['repeat']:
            loops = 1
        viewerState = ""
        qt_proc = subprocess.Popen(["/home/pi/RPiTest2", "--interval", imgInterval, "--blend", blendInterval, "--loops", str(loops)], stdin=subprocess.PIPE, stdout=subprocess.PIPE)



    def processImagesOnly(self):
        global playerState
        print "Processing only images."
        '''
        if self.config['repeat']:
            self.fbiImageLoop()
        else:
            self.processImagesOnce()
            stop()
        '''
        self.processImagesWithQtViewer()
        stop()

    def processVideosOnce(self):
        global playerState
        files = self.allVideos()
        files.sort()
        for file in files:
            # wait in case player is paused while switching file
            self.pauseevent.wait()
            if playerState == PLAYER_STARTED:
                if isVideo(file):
                    self.playVideo(file)

    def singleVideoLoop(self, filename):
        duration = self.getVideoDurationSeconds(filename)
        fullPath = self.mediaPath + filename
        #print "VIDEO PATH: ", fullPath
        looper1 = OMXPlayer(fullPath, start_playback=True)
        looper2 = OMXPlayer(fullPath, start_playback=True)
        looper2.toggle_pause()
        looper1Active = True
        pos = 0
        while self.config['repeat'] and playerState == PLAYER_STARTED:
            if looper1Active:
                pos = looper1.position
            else:
                pos = looper2.position
            # print "Position: ", pos
            if pos > duration -2:
                #print "TOGGLING LOOPERS..."
                # start other looper, wait 3 seconds and reload current looper for next round
                if looper1Active:
                    looper2.toggle_pause()
                    looper1.stop()
                    time.sleep(1)
                    looper1 = OMXPlayer(fullPath, start_playback=True)
                    looper1.toggle_pause()
                else:
                    looper1.toggle_pause()
                    looper2.stop()
                    time.sleep(1)
                    looper2 = OMXPlayer(fullPath, start_playback=True)
                    looper2.toggle_pause()
                looper1Active = not looper1Active
            time.sleep(0.1)
        if looper1:
            looper1.stop()
        if looper2:
            looper2.stop()

    def getVideoDurationSeconds(self, filename):
        proc = subprocess.Popen(['mplayer', '-vo', 'null', '-ao', 'null', '-frames', '0', '-identify', self.mediaPath + filename], stdout=subprocess.PIPE)
        output = proc.stdout.read()
        # print "Process Output: ", output
        ind = output.index('ID_LENGTH')
        start = ind + 10
        end = output.index('.',start)
        durStr = output[start:end]
        duration = int(durStr)
        #print "VIDEO DURATION: ",duration
        return duration

    def videoLoop(self):
        videos = self.allVideos()
        #if len(videos) == 1:
        #    self.singleVideoLoop(videos[0])
        #else:
        while self.config['repeat'] and playerState == PLAYER_STARTED:
            # check for config changes
            self.reloadConfig()
            self.processVideosOnce()

    def processVideosOnly(self):
        global playerState
        print "Processing only videos."
        if self.config['repeat']:
            self.videoLoop()
        else:
            self.processVideosOnce()
        stop()


    def playVideo(self,file):
        global playerState
        global videoPlaying
        # process video file -> omxplay will block until its done
        #print "Status PLAYER_STARTED: ", playerState == PLAYER_STARTED
        if playerState == PLAYER_STARTED:
            # blackout screen to avoid previous image to show through after video or when stopping
            self.blackout()
            fullPath = os.path.join(self.mediaPath, file)
            videoPlaying = True
            if platform.system() == 'Linux' and platform.linux_distribution()[0] == 'Ubuntu':
                subprocess.call([cwd + '/scripts/mplayerstart.sh', fullPath])
            else:
                subprocess.call([cwd + '/scripts/omxplay.sh', os.path.join(self.mediaPath, file)])
            videoPlaying = False


    def processAllFilesOnce(self):
        global playerState
        imgCmdList = ["sudo","fbi","--once","-noverbose","-readahead","-T","2"]
        files = self.allMediaFiles()
        files.sort()
        for file in files:
            # check file extension
            if isImage(file) and playerState == PLAYER_STARTED:
                # process image file
                curImgCmd = imgCmdList[:]
                curImgCmd.append(self.mediaPath + file)
                subProc = subprocess.Popen(curImgCmd)
                # sleep while image is shown, append a second for loading time
                #print "Showing image " + file + " for " + str(self.config['image_interval']) + " seconds"
                time.sleep(self.config['image_interval'] + 2    )
                subProc.kill()
                subProc.wait()
            elif isVideo(file):
                self.playVideo(file)

    def processAllFiles(self):
        global playerState
        print "Processing all files."
        if self.config['group_filetypes']:
            self.processImagesOnce()
            self.processVideosOnce()
            while self.config['repeat'] and playerState == PLAYER_STARTED:
                # check config for changes
                self.reloadConfig()
                self.processImagesOnce()
                self.processVideosOnce()
        else:
            self.processAllFilesOnce()
            while self.config['repeat'] and playerState == PLAYER_STARTED:
                # check config for changes
                self.reloadConfig()
                self.processAllFilesOnce()
        stop()

    def processSingleFile(self):
        global playerState
        global filenumber
        global cwd
        curFile = None
        files = sorted(getMediaFileList())
        while playerState == PLAYER_STARTED:
            if filenumber < len(files):
                newFile = files[filenumber]
                if curFile == None or not newFile == curFile:
                    if not curFile == None and curFile in self.allVideos():
                        # currently processed file is video --> stop video
                        if videoPlaying:
                            global videoPlaying
                            subprocess.call(['/home/pi/raspmedia/Raspberry/scripts/dbuscontrol.sh', 'stop'])
                            videoPlaying = False
                    curFile = newFile
                if curFile in self.allImages():
                    # selected file is image --> show with fbi
                    filePath = self.mediaPath + curFile
                    # link to new image to show
                    subprocess.call(["ln", "-s", "-f", os.path.join(self.mediaPath, curFile), cwd + '/img_al1.jpg'])
                    # check again for a file change in a second
                    time.sleep(1)
                elif curFile in self.allVideos():
                    # video command is blocking --> next check/switch when video is completely played
                    self.playVideo(curFile)
            else:
                # number beyond range of files --> show black screen
                cmdList = ['sudo','fbi','-noverbose','-T','2', '-a', cwd + '/raspblack.jpg']
                subprocess.call(cmdList)
                # check again in a second
                time.sleep(1)

    def blackout(self):
        # shows black screen, player stays in state STARTED!
        # link to blackout image
        subprocess.call(["ln", "-s", "-f", cwd + '/raspblack.jpg', cwd + '/img_al1.jpg'])

    def allImages(self):
        images = []
        for file in os.listdir(self.mediaPath):
            if file.endswith((SUPPORTED_IMAGE_EXTENSIONS)):
                images.append(file)
        return images

    def allVideos(self):
        videos = []
        for file in os.listdir(self.mediaPath):
            if file.endswith((SUPPORTED_VIDEO_EXTENSIONS)):
                videos.append(file)
        return videos

    def allMediaFiles(self):
        files = []
        for file in os.listdir(self.mediaPath):
            if file.endswith((SUPPORTED_VIDEO_EXTENSIONS)) or file.endswith((SUPPORTED_IMAGE_EXTENSIONS)):
                files.append(file)
        return files

    def processMediaFiles(self):
        global playerState
        global filenumber
        # if global filenumber is NONE process files as usual
        if filenumber == None:
            #print "Checking config on files to process:"
            #print self.config
            if self.config['image_enabled'] and self.config['video_enabled']:
                if len(self.allMediaFiles()) > 0:
                    self.processAllFiles()
                else:
                    stop()
            elif self.config['image_enabled']:
                if len(self.allImages()) > 0:
                    self.processImagesOnly()
                else:
                    stop()
            elif self.config['video_enabled']:
                if len(self.allVideos()) > 0:
                    self.processVideosOnly()
                else:
                    stop()
        else:
            # filenumber for processing a single file is set, only handle this single file if available
            self.processSingleFile()

        # set player state to stopped as processing is done at this point
        playerState = PLAYER_STOPPED

    def reloadConfig(self):
        self.config = configtool.readConfig()



def getMediaFileList():
    global mediaPath
    files = []
    for file in os.listdir(mediaPath):
        if isImage(file) or isVideo(file):
            files.append(file)
    return files

def getImageFilelist():
    global mediaPath
    files = []
    for file in os.listdir(mediaPath):
        if isImage(file):
            files.append(file)
    return files

def setMediaPath(curMediaPath):
    global mp_thread, mediaPath
    mediaPath = curMediaPath
    mp_thread.mediaPath = curMediaPath

def deleteFiles(files):
    global mediaPath
    global playerState
    restart = False
    if playerState == PLAYER_STARTED:
        stop()
        restart = True
        time.sleep(1)

    path = mediaPath
    thumbPath = mediaPath + '/thumbs/'
    if not path.endswith('/'):
        path += "/"
    for file in files:
        # delete image
        fullPath = os.path.join(path, file)
        if os.path.isfile(fullPath):
            os.remove(fullPath)
        # delete thumbnail
        fullPath = os.path.join(thumbPath, file)
        if os.path.isfile(fullPath):
            os.remove(fullPath)

    if restart:
        play()
        time.sleep(1)

def isImage(filename):
    return filename.endswith((SUPPORTED_IMAGE_EXTENSIONS))

def isVideo(filename):
    return filename.endswith((SUPPORTED_VIDEO_EXTENSIONS))

def identifySelf():
    global identifyFlag, mp_thread, playerState, previousState
    previousState = playerState
    if playerState == PLAYER_STARTED:
        stop()
        time.sleep(0.5)
    identifyFlag = True
    config = configtool.readConfig()
    ImageIdentifier.IdentifyImage(config['player_name'])
    #print "Image prepared..."
    mp_thread.identify_event.clear()
    play()

def identifyDone():
    global identifyFlag, mp_thread, previousState
    if previousState == PLAYER_STOPPED:
        stop()
    identifyFlag = False
    mp_thread.identify_event.set()

def play():
    global playerState
    playerState = PLAYER_STARTED
    global mp_thread

    # media file processing in separate thread
    if not mp_thread.isAlive():
        mp_thread.start()
    mp_thread.runevent.set()
    # check pause event and set if cleared
    if not mp_thread.pauseevent.is_set():
        mp_thread.pauseevent.set()
    print "Mediaplayer running in thread: ", mp_thread.name

def startFileNumber(number):
    global playerState
    global filenumber
    if playerState == PLAYER_STARTED:
        stop()
    # wait one second to let the player change to stopped state
    time.sleep(1)
    filenumber = number
    time.sleep(1)
    play()

def stop():
    global mp_thread
    global playerState
    global filenumber
    global videoPlaying
    playerState = PLAYER_STOPPED
    mp_thread.runevent.clear()
    # check for fbi and omxplayer processes and terminate them
    # processtool.killProcesses('fbi')
    
    # stop omx player instance if running
    if videoPlaying:
        subprocess.call(['/home/pi/raspmedia/Raspberry/scripts/dbuscontrol.sh', 'stop'])
        videoPlaying = False

    # stop qt viewer if currently running
    if not qt_proc == None:
        qt_proc.kill()
        qt_proc = None

def pause():
    global videoPlaying
    global playerState
    global mp_thread
    print "Toggling paused state..."
    
    # toggle thread pause event
    if mp_thread.pauseevent.is_set():
        mp_thread.pauseevent.clear()
    else:
        mp_thread.pauseevent.set()
    # toggle video playback --> same command will pause/resume
    if videoPlaying:
        subprocess.call(['/home/pi/raspmedia/Raspberry/scripts/dbuscontrol.sh', 'pause'])

def setState(state):
    global playerState
    global blackout
    global filenumber
    global mp_thread
    config = configtool.readConfig()
    # 0 = stop, 1 = play
    if state == 0:
        if playerState == PLAYER_STARTED:
            stop()
        blackout = False
    elif state == 1:
        if playerState == PLAYER_STOPPED:
            play()
        elif playerState == PLAYER_STARTED and blackout:
            stop()
            time.sleep(1)
            blackout = False	    
            play()
        blackout = False
    elif state == 2:
        if playerState == PLAYER_STARTED:
            stop()
        blackout = True
        time.sleep(1)
        blackout = True
        play()
    elif state == 3:
        pause()

def setMediaFileNumber(num):
    global playerState
    global filenumber
    restart = False
    
    time.sleep(1)
    if num == -1 or filenumber == None:
        # stop player for resetting or initially setting file number
        if playerState == PLAYER_STARTED and not blackout:
            restart = True
            stop()
        if num == -1:
            filenumber = None
        else:
            filenumber = num
    else:
        filenumber = num
    if restart:
        time.sleep(1)
        play()
    
def nextFile():
    global filenumber
    num = -1
    if filenumber == None:
        num = 0
    else:
        files = getMediaFileList()
        num = (filenumber + 1) % len(files)
    setMediaFileNumber(num)

def prevFile():
    global filenumber
    num = -1
    if filenumber == None:
        num = 0
    else:
        files = getMediaFileList()
        num = filenumber - 1
        if num == -1:
            num = len(files) - 1
    setMediaFileNumber(num)

def main():
    global cwd, mp_thread, playerState
    print "PLAYER CWD: " + cwd
    if not mp_thread:
        mp_thread = MediaPlayer()
        mp_thread.daemon = True
    playerState = PLAYER_STOPPED
    mp_thread.start()

main()
