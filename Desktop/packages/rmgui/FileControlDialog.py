import wx
import sys, platform
from packages.rmnetwork import netutil
import packages.rmnetwork as network
from packages.rmnetwork.constants import *
from packages.lang.Localizer import *

################################################################################
# DIALOG FOR WIFI CONFIG #######################################################
################################################################################
class FileControlDialog(wx.Dialog):
    def __init__(self,parent,id,title,host,files):
        wx.Dialog.__init__(self,parent,id,title)
        self.parent = parent
        self.host = host
        self.files = files
        self.mainSizer = wx.BoxSizer(wx.VERTICAL)
        self.__InitUI()
        self.SetSizerAndFit(self.mainSizer)
        self.Center()

    def __InitUI(self):
        # info string
        info = wx.StaticText(self,-1,label="Double click file to show on player")

        #list of files on player
        self.fileList = wx.ListCtrl(self,-1,size=(260,200),style=wx.LC_REPORT|wx.SUNKEN_BORDER)
        # print "Showing list..."
        self.fileList.Show(True)
        self.fileList.InsertColumn(0,tr("filename"), width = 250)
        self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.FileDoubleClicked, self.fileList)

        for curFile in reversed(self.files):
            idx = self.fileList.InsertStringItem(self.fileList.GetItemCount(), curFile)

        # play stop pause close and clear buttons
        play = wx.Button(self,-1,label="Play")
        stop = wx.Button(self,-1,label="Stop")
        pause = wx.Button(self,-1,label="Pause")
        clear = wx.Button(self,-1,label="Clear")
        close = wx.Button(self,-1,label="Close")

        play.Bind(wx.EVT_BUTTON, self.PlayClicked)
        stop.Bind(wx.EVT_BUTTON, self.StopClicked)
        pause.Bind(wx.EVT_BUTTON, self.PauseClicked)
        clear.Bind(wx.EVT_BUTTON, self.ClearClicked)
        close.Bind(wx.EVT_BUTTON, self.CloseClicked)

        # arrange UI elements in sizers
        btnSizer = wx.BoxSizer()
        btnSizerLeft = wx.BoxSizer(wx.VERTICAL)
        btnSizerRight = wx.BoxSizer(wx.VERTICAL)
        btnSizerLeft.Add(play, flag=wx.ALL, border=2)
        btnSizerLeft.Add(stop, flag=wx.ALL, border=2)
        btnSizerRight.Add(pause, flag=wx.ALL, border=2)
        btnSizerRight.Add(clear, flag=wx.ALL, border=2)
        btnSizer.Add(btnSizerLeft)
        btnSizer.Add(btnSizerRight)

        self.mainSizer.Add(info, flag=wx.ALL, border=10)
        self.mainSizer.Add(self.fileList,flag=wx.ALL, border=10)
        self.mainSizer.Add(btnSizer, flag=wx.ALL | wx.ALIGN_CENTER_HORIZONTAL, border=10)
        self.mainSizer.Add(close, flag=wx.ALL | wx.ALIGN_CENTER_HORIZONTAL, border=15)

    def FileDoubleClicked(self, event):
        index = self.fileList.GetFirstSelected()
        msgData = network.messages.getMessage(PLAYER_SET_FILENUMBER, ["-i", str(index)])
        network.udpconnector.sendMessage(msgData, self.host)

    def PlayClicked(self, event):
        msgData = network.messages.getMessage(PLAYER_START)
        network.udpconnector.sendMessage(msgData, self.host)

    def StopClicked(self, event):
        msgData = network.messages.getMessage(PLAYER_STOP)
        network.udpconnector.sendMessage(msgData, self.host)

    def PauseClicked(self, event):
        msgData = network.messages.getMessage(PLAYER_PAUSE)
        network.udpconnector.sendMessage(msgData, self.host)

    def ClearClicked(self, event):
        msgData = network.messages.getMessage(PLAYER_CLEAR_FILENUMBER)
        network.udpconnector.sendMessage(msgData, self.host)

    def CloseClicked(self, event):
        self.EndModal(wx.ID_OK)
        self.Destroy()
