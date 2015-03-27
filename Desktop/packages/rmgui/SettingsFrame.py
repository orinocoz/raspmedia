import packages.rmnetwork as network
import packages.rmutil as rmutil
from packages.rmgui import *
import WifiDialog as wifi
from packages.rmnetwork.constants import *
from packages.lang.Localizer import *
import os, sys, platform, ast, time, threading, shutil

import wx
if platform.system() == "Linux":
    from wx.lib.pubsub import setupkwargs
    from wx.lib.pubsub import pub as Publisher
else:
    from wx.lib.pubsub import pub as Publisher
from wx.lib.wordwrap import wordwrap

################################################################################
# SETTINGS FRAME ###############################################################
################################################################################
class SettingsFrame(wx.Frame):
    def __init__(self,parent,id,title,host,config):
        wx.Frame.__init__(self,parent,id,title,size=(400,300))
        self.parent = parent
        self.Bind(wx.EVT_CLOSE, self.Close)
        self.host = host['addr']
        self.name = host['name']
        self.prgDialog = None
        self.Initialize()
        self.SetSizerAndFit(self.configSizer)

        # Create an accelerator table
        sc_wifi_id = wx.NewId()
        sc_close_id = wx.NewId()
        self.Bind(wx.EVT_MENU, self.Close, id=sc_close_id)
        self.Bind(wx.EVT_MENU, self.ShowWifiSettings, id=sc_wifi_id)

        self.accel_tbl = wx.AcceleratorTable([(wx.ACCEL_CTRL, ord('W'), sc_close_id),
                                             (wx.ACCEL_SHIFT, ord('W'), sc_wifi_id)
                                            ])
        self.SetAcceleratorTable(self.accel_tbl)

        self.Show()
        self.UpdateUI(config, True)

    def Close(self, event=None):
        Publisher.unsubAll()
        self.parent.SettingsClosedWithConfig(self.config)
        self.Destroy()

    def Initialize(self):
        self.configSizer = wx.GridBagSizer()
        # checkboxes
        self.cbImgEnabled = wx.CheckBox(self, -1, tr("enable_images"))
        self.cbVidEnabled = wx.CheckBox(self, -1, tr("enable_videos"))
        self.cbAutoplay = wx.CheckBox(self, -1, tr("autoplay"))
        self.cbRepeat = wx.CheckBox(self, -1, tr("repeat"))

        # interval, player name and ip
        intervalLabel = wx.StaticText(self,-1,label=tr("image_interval")+" (s):")
        self.imgIntervalLabel = wx.StaticText(self,-1,label="")
        blendInterval = wx.StaticText(self,-1,label="Blend Interval (ms):")
        self.blendIntervalLabel = wx.StaticText(self,-1,label="")
        nameLabel = wx.StaticText(self,-1,label=tr("player_name")+":")
        self.playerNameLabel = wx.StaticText(self,-1,label="")
        addrLabel = wx.StaticText(self,-1,label=tr("ip_address")+":")
        playerAddr = wx.StaticText(self,-1,label=self.host)

        updateBtn = wx.Button(self, -1, tr("update_player"))
        setupWifi = wx.Button(self, -1, tr("setup_wifi"), size = updateBtn.GetSize())

        self.editInterval = wx.Button(self,-1,label="...",size=(27,25))
        self.editName = wx.Button(self,-1,label="...",size=(27,25))
        self.editBlend = wx.Button(self,-1,label="...",size=(27,25))

        # combo box for available transitions
        blendTypeLabel = wx.StaticText(self,-1,label="Blend Type:")
        self.transitions = ['Blend', 'Zoom', 'Slide', 'Flip', 'Flip Vertical', 'Flip Diagonal']
        self.combo = wx.ComboBox(self, -1, choices=self.transitions, size = (150,25), style = wx.CB_READONLY)
        self.Bind(wx.EVT_COMBOBOX, self.TransitionSelected, self.combo)

        # horizontal divider line
        line = wx.StaticLine(self,-1,size=(260,2))

        # set names for further identifying
        self.cbImgEnabled.SetName('image_enabled')
        self.cbVidEnabled.SetName('video_enabled')
        self.cbAutoplay.SetName('autoplay')
        self.cbRepeat.SetName('repeat')
        self.editInterval.SetName('btn_image_interval')
        self.editName.SetName('btn_player_name')
        self.editBlend.SetName('btn_blend_interval')
        updateBtn.SetName('btn_update')
        setupWifi.SetName('btn_setup_wifi')

        # bind UI element events
        self.Bind(wx.EVT_CHECKBOX, self.CheckboxToggled, self.cbImgEnabled)
        self.Bind(wx.EVT_CHECKBOX, self.CheckboxToggled, self.cbVidEnabled)
        self.Bind(wx.EVT_CHECKBOX, self.CheckboxToggled, self.cbAutoplay)
        self.Bind(wx.EVT_CHECKBOX, self.CheckboxToggled, self.cbRepeat)
        self.Bind(wx.EVT_BUTTON, self.ButtonClicked, self.editInterval)
        self.Bind(wx.EVT_BUTTON, self.ButtonClicked, self.editName)
        self.Bind(wx.EVT_BUTTON, self.ButtonClicked, self.editBlend)
        self.Bind(wx.EVT_BUTTON, self.ButtonClicked, updateBtn)
        self.Bind(wx.EVT_BUTTON, self.ButtonClicked, setupWifi)

        self.configSizer.Add(self.cbImgEnabled, (0,0), flag=wx.TOP | wx.LEFT, border = 5)
        self.configSizer.Add(self.cbVidEnabled, (1,0), flag=wx.LEFT, border = 5)
        self.configSizer.Add(self.cbAutoplay, (0,1), flag=wx.TOP, border = 5)
        self.configSizer.Add(self.cbRepeat, (1,1))
        self.configSizer.Add(intervalLabel, (3,0), flag=wx.ALIGN_CENTER_VERTICAL | wx.LEFT, border = 5)
        self.configSizer.Add(self.imgIntervalLabel, (3,1), flag=wx.ALIGN_CENTER_VERTICAL)
        self.configSizer.Add(self.editInterval, (3,3))
        self.configSizer.Add(blendInterval, (4,0), flag=wx.ALIGN_CENTER_VERTICAL | wx.LEFT, border = 5)
        self.configSizer.Add(self.blendIntervalLabel, (4,1), flag=wx.ALIGN_CENTER_VERTICAL)
        self.configSizer.Add(self.editBlend, (4,3))
        self.configSizer.Add(blendTypeLabel, (5,0), flag=wx.ALIGN_CENTER_VERTICAL | wx.LEFT, border = 5)
        self.configSizer.Add(self.combo, (5,1), span=(1,2), flag=wx.ALIGN_CENTER_VERTICAL)
        self.configSizer.Add(nameLabel, (6,0), flag=wx.ALIGN_CENTER_VERTICAL | wx.LEFT, border = 5)
        self.configSizer.Add(self.playerNameLabel, (6,1), flag=wx.ALIGN_CENTER_VERTICAL)
        self.configSizer.Add(self.editName, (6,3))
        self.configSizer.Add(addrLabel, (7,0), flag = wx.ALIGN_CENTER_VERTICAL | wx.LEFT | wx.BOTTOM, border = 5)
        self.configSizer.Add(playerAddr, (7,1), flag = wx.ALIGN_CENTER_VERTICAL | wx.BOTTOM, border = 5)
        self.configSizer.Add(setupWifi, (0,4), flag = wx.ALL, border = 5)
        self.configSizer.Add(updateBtn, (1,4), flag = wx.ALL, border = 5)
        self.configSizer.Add(line, (2,0), span=(1,6), flag=wx.TOP | wx.BOTTOM, border=5)


    def UpdateUI(self, config, isDict=False):
        if isDict:
            configDict = config
        else:
            configDict = ast.literal_eval(config)
        self.config = configDict
        if not "blend_type" in configDict:
            configDict["blend_type"] = "Blend"
        self.SelectTransition(configDict['blend_type'])
        self.cbImgEnabled.SetValue(configDict['image_enabled'])
        self.cbVidEnabled.SetValue(configDict['video_enabled'])
        self.cbRepeat.SetValue(configDict['repeat'])
        self.cbAutoplay.SetValue(configDict['autoplay'])
        self.imgIntervalLabel.SetLabel(str(configDict['image_interval']))
        self.blendIntervalLabel.SetLabel(str(configDict['image_blend_interval']))
        self.playerNameLabel.SetLabel(str(configDict['player_name']))

    def SelectTransition(self, transition):
        index = self.transitions.index(transition)
        self.combo.SetSelection(index)

    def TransitionSelected(self, event):
        blendType = self.combo.GetValue()
        msgData = network.messages.getConfigUpdateMessage("blend_type", str(blendType))
        network.udpconnector.sendMessage(msgData, self.host)
        time.sleep(0.2)
        self.LoadConfig()

    def LoadConfig(self):
        Publisher.subscribe(self.UpdateUI, 'config')
        Publisher.subscribe(self.UdpListenerStopped, 'listener_stop')
        # print "Observers registered..."
        msgData = network.messages.getMessage(CONFIG_REQUEST)
        dlgStyle =  wx.PD_AUTO_HIDE
        #self.prgDialog = wx.ProgressDialog("Loading...", "Loading configuration from player...", maximum = 0, parent = self, style = dlgStyle)
        #self.prgDialog.Pulse()
        network.udpconnector.sendMessage(msgData, self.host)

    def UdpListenerStopped(self):
        if self.prgDialog:
            self.prgDialog.Update(100)
            self.prgDialog.Destroy()
            #self.prgDialog = None

    def ButtonClicked(self, event):
        button = event.GetEventObject()
        if button.GetName() == 'btn_image_interval':
            dlg = wx.TextEntryDialog(self, tr("new_interval")+":", tr("image_interval"), self.imgIntervalLabel.GetLabel())
            if dlg.ShowModal() == wx.ID_OK:
                try:
                    newInterval = int(dlg.GetValue())
                    # self.imgIntervalLabel.SetLabel(str(newInterval))
                    msgData = network.messages.getConfigUpdateMessage("image_interval", newInterval)
                    network.udpconnector.sendMessage(msgData, self.host)
                    time.sleep(0.2)
                    self.LoadConfig()
                except Exception, e:
                    error = wx.MessageDialog(self, tr("enter_valid_number"), tr("invalid_interval"), wx.OK | wx.ICON_EXCLAMATION)
                    error.ShowModal()

            dlg.Destroy()
        elif button.GetName() == 'btn_blend_interval':
            dlg = wx.TextEntryDialog(self, tr("new_interval")+":", "Blend Interval", self.blendIntervalLabel.GetLabel())
            if dlg.ShowModal() == wx.ID_OK:
                try:
                    newBlendInterval = int(dlg.GetValue())
                    # self.imgIntervalLabel.SetLabel(str(newBlendInterval))
                    msgData = network.messages.getConfigUpdateMessage("image_blend_interval", newBlendInterval)
                    network.udpconnector.sendMessage(msgData, self.host)
                    time.sleep(0.2)
                    self.LoadConfig()
                except Exception, e:
                    error = wx.MessageDialog(self, tr("enter_valid_number"), "Blend Interval", wx.OK | wx.ICON_EXCLAMATION)
                    error.ShowModal()

            dlg.Destroy()
        elif button.GetName() == 'btn_player_name':
            dlg = wx.TextEntryDialog(self, tr("new_name")+":", tr("player_name"), self.playerNameLabel.GetLabel())
            if dlg.ShowModal() == wx.ID_OK:
                newName = dlg.GetValue()
                self.playerNameLabel.SetLabel(newName)
                msgData = network.messages.getConfigUpdateMessage("player_name", str(newName))
                network.udpconnector.sendMessage(msgData, self.host)
                time.sleep(0.2)
                self.LoadConfig()
            dlg.Destroy()
        elif button.GetName() == 'btn_update':
            Publisher.subscribe(self.RebootComplete, 'boot_complete')

            self.prgDialog = wx.ProgressDialog("Updating...", wordwrap(tr("update_message"), 350, wx.ClientDC(self)))
            self.prgDialog.Pulse()

            msgData = network.messages.getMessage(PLAYER_UPDATE)
            network.udpconnector.sendMessage(msgData, self.host, UDP_UPDATE_TIMEOUT)
        elif button.GetName() == 'btn_setup_wifi':
            self.ShowWifiSettings()

    def ShowWifiSettings(self, event=None):
        wifiDlg = wifi.WifiDialog(self, -1, tr("wifi_settings"), self.host)
        wifiDlg.ShowModal()

    def RebootComplete(self):
        # print "SETTING FRAME - BOOT COMPLETE RECEIVED"
        self.prgDialog.Update(100)
        if platform.system() == "Windows":
            self.prgDialog.Destroy()
        dlg = wx.MessageDialog(self,"Reboot complete!","",style=wx.OK)
        dlg.Show()
        if platform.system() == "Windows":
            dlg.Destroy()

    def CheckboxToggled(self, event):
        checkbox = event.GetEventObject()
        # print checkbox.GetName()
        msgData = network.messages.getConfigUpdateMessage(checkbox.GetName(), checkbox.IsChecked())
        network.udpconnector.sendMessage(msgData, self.host)
        self.LoadConfig()
