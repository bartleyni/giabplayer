import time
import subprocess
import urllib2
import os
import glob
import threading
import pifacecad
import re
from pifacecad.tools.question import LCDQuestion
from vlcclient import VLCClient

### Threaded Player GIAB Micro Player ###
### Nick Bartley 2013 ###

### Thread for Display Manager ###
### Thread for Player Status ###
### General Control Thread ###

# GLOBALS

#Available player options
Options = [\
	("Stream", "URB", "http://people.bath.ac.uk/su9urb/audio/urb-hi.m3u"), \
	("Stream", "JackFM", "http://stream1.radiomonitor.com/JackBristol-128.m3u"), \
	("Folder", "Pop House Music", "giabplayer/PopHouse/"), \
	("Folder", "ICIA House Music", "giabplayer/ICIAHouse/"), \
	("File", "Applause", "giabplayer/cannedApplause.wav"), \
	("File", "Ring Out", "giabplayer/MoneyForNothing.mp3"), \
	("Sting", "Stings", "giabplayer/Stings/"), \
	("Help", "Help", "giabplayer/Help.mp3"), \
	("Folder", "USB Stick", "/media/usb/") \
	]

#Display Control Variables
DisplayLineOne = None
DisplayLineTwo = None

#Player Control Variables
PlayerControl = None
PlayerStatus = None
PlayerSource = None
StatusFlag = False

#General Control Variables
LastSting = 0
SelectedMode = 0
DISPLAY = pifacecad.PiFaceCAD()
PLAYER_LOCK = threading.Lock()
Internet = False

#Checks to see if there is an internet connection
def InternetOn():
    try:
        Response=urllib2.urlopen('http://74.125.228.100',timeout=1)
        return True
    except urllib2.URLError as err: pass
    return False

#Polls for network connection and will persistantly try to connect to wifi
def CheckInternet(Delay):
	global Internet
	LastInternet = 0
	ExitFlag = False
	
	while True:
		if ExitFlag:
			thread.exit()
		PLAYER_LOCK.acquire()
		Internet = InternetOn()
		PLAYER_LOCK.release()
		if Internet == True and LastInternet == False:
			print "Internet Connected"

		if Internet == False and LastInternet == True:
			print "Internet Disconnected"
			WLANOff = subprocess.Popen(["sudo", "ifconfig", "wlan0", "down"])
			ETHOff = subprocess.Popen(["sudo", "ifconfig", "eth0", "down"])
			WLANOn = subprocess.Popen(["sudo", "ifconfig", "wlan0", "up"])
			ETHOn = subprocess.Popen(["sudo", "ifconfig", "eth0", "up"])
		
		LastInternet = Internet
		time.sleep(Delay)
	
#Controls the LCD display
def DisplayUpdate():
	
	global DisplayLineOne
	global DisplayLineTwo	
	
	DisplayLineOne = " "
	DisplayLineTwo = " "
	LastDisplayLineOne = None
	LastDisplayLineTwo = None
	
	while True:
		PLAYER_LOCK.acquire()
		if DisplayLineOne <> LastDisplayLineOne:
			DISPLAY.lcd.set_cursor(0, 0)
			LineOne = DisplayLineOne[0:16]
			DISPLAY.lcd.write(LineOne.ljust(16))
			LastDisplayLineOne = DisplayLineOne
		if DisplayLineTwo <> LastDisplayLineTwo :
			DISPLAY.lcd.set_cursor(0, 1)
			LineTwo = DisplayLineTwo[0:16]
			DISPLAY.lcd.write(LineTwo.ljust(16))
			LastDisplayLineTwo = DisplayLineTwo
		PLAYER_LOCK.release()
		
		time.sleep(0.01)

#Controls VLC Player
def PlayerOperation():
	
	global PlayerStatus
	global DisplayLineOne
	global DisplayLineTwo
	global StatusFlag
	
	PlayingTitle = " "
	PlayerStatus = " "
	VLC_STATUS= VLCClient("127.0.0.1",4212,"admin",1)
	
	while True:
		
		#PLAYER_LOCK.acquire()
		VLC_STATUS.connect()
		
		PlayerState = VLC_STATUS.playing()
		
		if PlayerState == "0":
			PlayerStatus = "Stopped"
		else:
			PlayerStatus = "Playing"
			
		PlayingTitle = VLC_STATUS.title()
		
		VLC_STATUS.disconnect()
		#PLAYER_LOCK.release()
		
		if StatusFlag == True:
			DisplayLineTwo = PlayerStatus.center(16)
			time.sleep(1.5)
			if PlayerState <> "0":
				DisplayLineTwo = PlayingTitle.center(16)
			time.sleep(1)
			
		if PlayerState == "0":
			StatusFlag = False
			
		time.sleep(0.5)
		

#GIAB Player Controlling System
def ModeSelector(CurrentMode):
	
	global HighlightedMode
	global DisplayLineOne
	global DisplayLineTwo
	global SelectedMode

	HighlightedMode = CurrentMode
	LastModeOption = len(Options)-1
	
	DisplayLineOne = "Mode:"
	DisplayLineTwo = Options[HighlightedMode][1].center(16)
	
	SelectorMode = True
	
	while SelectorMode == True:
		
		if DISPLAY.switches[7].value == 1:
			HighlightedMode = HighlightedMode + 1
			if HighlightedMode > LastModeOption:
				HighlightedMode = 0
			DisplayLineTwo = Options[HighlightedMode][1].center(16)
			time.sleep(0.3)
			
		if DISPLAY.switches[6].value == 1:
			HighlightedMode = HighlightedMode - 1
			if HighlightedMode < 0:
				HighlightedMode = LastModeOption
			DisplayLineTwo = Options[HighlightedMode][1].center(16)
			time.sleep(0.3)
		
		if DISPLAY.switches[5].value == 1:
			PLAYER_LOCK.acquire()
			SelectedMode = HighlightedMode
			
			OptionName = Options[SelectedMode][1]
			DisplayLineTwo = " "
			PLAYER_LOCK.release()
			LoadPlayer()
			return SelectedMode
			SelectorMode = False
		
		if DISPLAY.switches[0].value == 1:
			PLAYER_LOCK.acquire()
			SelectedMode = HighlightedMode
			
			OptionName = Options[SelectedMode][1]
			DisplayLineTwo = " "
			PLAYER_LOCK.release()
			LoadPlayer()
			time.sleep (0.3)
			StatusFlag = True
			VLC = VLCClient("127.0.0.1",4212,"admin",1)
			VLC.connect()
			if Options[SelectedMode][0] == "Folder":
				VLC.randomon()
			VLC.play()
			VLC.disconnect()
			StatusFlag = True
			return SelectedMode
			SelectorMode = False
			
		if DISPLAY.switches[4].value == 1:
			DISPLAY.lcd.clear()
			DISPLAY.lcd.home()
			DisplayLineOne = Options[SelectedMode][1]
			StatusFlag = True
			SelectorMode = False
			return

#PlayerLoad
def LoadPlayer():
	
	global PlayerControl

	global PlayerSource
	global LastSting
	global SelectedMode
	global DisplayLineOne
	
	VLC = VLCClient("127.0.0.1",4212,"admin",1)
	
	OptionType = Options[SelectedMode][0]
	OptionName = Options[SelectedMode][1]
	OptionAddress = Options[SelectedMode][2]

	VLC.connect()

	if OptionType == "Stream":
		DisplayLineOne = OptionName
		PlayerSource = OptionAddress
		VLC.clear()
		VLC.enqueue(PlayerSource)
		VLC.loopoff()
	if OptionType == "Folder":
		DisplayLineOne = OptionName
		PlayerSource = OptionAddress
		VLC.clear()
		VLC.enqueue(PlayerSource)
		VLC.loopon()
		VLC.randomon()
	if OptionType == "File":
		DisplayLineOne = OptionName
		PlayerSource = OptionAddress
		VLC.clear()
		VLC.enqueue(PlayerSource)
		VLC.loopoff()
	if OptionType == "Help":
		DisplayLineOne = OptionName
		PlayerSource = OptionAddress
		VLC.clear()
		VLC.enqueue(PlayerSource)
		VLC.loopon()
		#VLC.play()
	if OptionType == "Sting":
		Sting = str(LastSting+1)
		DisplayLineOne = "Sting: "+Sting
		StingCounter = len(glob.glob1(OptionAddress,"*.mp3"))-1
		LastSting = LastSting+1
		if LastSting > StingCounter:
			LastSting = 0
		PlayerSource = OptionAddress+Sting+".mp3"
		VLC.clear()
		VLC.enqueue(OptionAddress+Sting+".mp3")
		VLC.loopoff()
		VLC.randomoff()
	
	VLC.disconnect()
	
#Play Button
def PlayButton(event):
	global StatusFlag
	global SelectedMode
	
	StatusFlag = True
	VLC = VLCClient("127.0.0.1",4212,"admin",1)
	VLC.connect()
	if Options[SelectedMode][0] == "Folder":
		VLC.randomon()
		VLC.next()
	VLC.play()
	VLC.disconnect()
	StatusFlag = True

#Stop Button
def StopButton(event):
	
	global SelectedMode
	global StatusFlag
	
	if Options[SelectedMode][0] == "Sting":
		LoadPlayer()
	VLC = VLCClient("127.0.0.1",4212,"admin",1)
	VLC.connect()
	VLC.stop()
	VLC.disconnect()

#Mode Button
def ModeButton(event):
	global SelectedMode
	global StatusFlag
	
	StatusFlag = False
	ModeSelector(SelectedMode)

#Reset Network
def NetResetButton(event):
	global DisplayLineOne
	global DisplayLineTwo
	VLC = VLCClient("127.0.0.1",4212,"admin",1)
	VLC.connect()
	VLC.stop()
	VLC.disconnect()
	time.sleep(1)
	DISPLAY.lcd.clear()
	DISPLAY.lcd.home()
	DisplayLineOne = "Network Reset".center(16)
	time.sleep(3)
	NETWORK_RESTART = subprocess.Popen(["sudo", "/etc/init.d/networking", "restart"])

#Shutdown Pi
def ShutdownButton(event):
	global DisplayLineOne
	global DisplayLineTwo
	global SelectedMode
	global StatusFlag
	
	PLAYER_LOCK.acquire()
	StatusFlag = False
	PLAYER_LOCK.release()
	
	time.sleep(1)
	DISPLAY.lcd.clear()
	DISPLAY.lcd.home()
	DisplayLineOne = "Shutdown...".center(16)
	DisplayLineTwo = "Press again...".center(16)
	while True:
		if DISPLAY.switches[2].value == 1:
			VLC = VLCClient("127.0.0.1",4212,"admin",1)
			VLC.connect()
			VLC.stop()
			VLC.disconnect()
			time.sleep(2)
			DISPLAY.lcd.clear()
			DISPLAY.lcd.home()
			DisplayLineOne = "Shutdown...".center(16)
			SHUTDOWN = subprocess.Popen(["sudo", "halt"])
			for i in range (10, 0, -1):
				DisplayLineTwo = str(i).center(16)
				time.sleep(1)
		if DISPLAY.switches[4].value == 1:
			DISPLAY.lcd.clear()
			DISPLAY.lcd.home()
			PLAYER_LOCK.acquire()
			DisplayLineOne = Options[SelectedMode][1]
			StatusFlag = True
			PLAYER_LOCK.release()
			return

#Reboot Pi
def RebootButton(event):
	global DisplayLineOne
	global DisplayLineTwo
	global StatusFlag
	global SelectedMode
	
	PLAYER_LOCK.acquire()
	StatusFlag = False
	PLAYER_LOCK.release()
	
	time.sleep(1)
	DISPLAY.lcd.clear()
	DISPLAY.lcd.home()
	DisplayLineOne = "Rebooting...".center(16)
	DisplayLineTwo = "Press again...".center(16)
	while True:
		if DISPLAY.switches[3].value == 1:
			VLC = VLCClient("127.0.0.1",4212,"admin",1)
			VLC.connect()
			VLC.stop()
			VLC.disconnect()
			time.sleep(2)
			DISPLAY.lcd.clear()
			DISPLAY.lcd.home()
			DisplayLineOne = "Rebooting...".center(16)
			SHUTDOWN = subprocess.Popen(["sudo", "reboot"])
			for i in range (10, 0, -1):
				DisplayLineTwo = str(i).center(16)
				time.sleep(1)
		if DISPLAY.switches[4].value == 1:
			DISPLAY.lcd.clear()
			DISPLAY.lcd.home()
			PLAYER_LOCK.acquire()
			DisplayLineOne = Options[SelectedMode][1]
			StatusFlag = True
			PLAYER_LOCK.release()
			return
	
#System Initialization
def Initialize():
	
	WLANOff = subprocess.Popen(["sudo", "ifconfig", "wlan0", "down"])
	WLANOn = subprocess.Popen(["sudo", "ifconfig", "wlan0", "up"])
	
	#PLAYER_PROCESS = subprocess.Popen(["/usr/bin/vlc", "-I", "dummy", "--volume", "250", "--intf", "telnet"])
	PLAYER_PROCESS = subprocess.Popen(["/usr/bin/vlc", "-I", "dummy", "--volume", "250", "--intf", "telnet", "--lua-config", "telnet={host='0.0.0.0:4212'}"])
	#PLAYER_PROCESS = subprocess.Popen(["/usr/bin/vlc", "-I", "dummy", "--volume", "250", "--intf", "telnet", "--lua-config", "telnet={host='0.0.0.0:4212'}", "--sout", "'#std{access=http,mux=ts,dst=192.168.0.5:1234}'"])
	
	
	DISPLAY.lcd.backlight_on()
	DISPLAY.lcd.blink_off()
	DISPLAY.lcd.cursor_off()
	
	CONNECTED = pifacecad.LCDBitmap([0b01110, 0b10001, 0b00000, 0b00100, 0b01010, 0b00000, 0b00100, 0b00000])
	DISPLAY.lcd.store_custom_bitmap(0, CONNECTED)
	
	DISPLAY.lcd.clear()
	DISPLAY.lcd.home()
	DISPLAY.lcd.write("GIAB Micro")
	DISPLAY.lcd.set_cursor(0, 1)
	DISPLAY.lcd.write("Version 2.0")
	
	time.sleep(2.5)
	
	DISPLAY.lcd.clear()
	DISPLAY.lcd.home()
	DISPLAY.lcd.write("Copyright 2013")
	DISPLAY.lcd.set_cursor(0, 1)
	DISPLAY.lcd.write("Nick Bartley")
	
	time.sleep(2.5)
	
	DISPLAY.lcd.clear()
	DISPLAY.lcd.home()
	DISPLAY.lcd.write("Internet")
	DISPLAY.lcd.set_cursor(0, 1)
	if InternetOn():
		DISPLAY.lcd.write("Connected")
		DISPLAY.lcd.set_cursor(15, 1)
		DISPLAY.lcd.write_custom_bitmap(0)
	else:
		DISPLAY.lcd.write("Disconnected")
	
	time.sleep(2.5)
	
	DISPLAY.lcd.clear()
	LISTENER = pifacecad.SwitchEventListener(chip=DISPLAY)
	LISTENER.register(0, pifacecad.IODIR_FALLING_EDGE, PlayButton)
	LISTENER.register(1, pifacecad.IODIR_FALLING_EDGE, StopButton)
	LISTENER.register(2, pifacecad.IODIR_FALLING_EDGE, ShutdownButton)
	LISTENER.register(3, pifacecad.IODIR_FALLING_EDGE, RebootButton)
	LISTENER.register(4, pifacecad.IODIR_FALLING_EDGE, ModeButton)
	LISTENER.activate()
	
#Main Program
def Main():
	Initialize()
	time.sleep(0.5)
	ModeSelector(SelectedMode)
	ExitFlag = False
	
	while True:
		#Comment
		if ExitFlag:
			return
		time.sleep(0.5)

#Thread for Main Control
class ControlThread (threading.Thread):
    def __init__(self, threadID, name):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name
    def run(self):
        print "Starting " + self.name
        Main()
        print "Exiting " + self.name

#Thread for Display
class DisplayThread (threading.Thread):
    def __init__(self, threadID, name):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name
    def run(self):
        print "Starting " + self.name
        DisplayUpdate()
        print "Exiting " + self.name
		
#Thread for VLC Player Status
class PlayerThread (threading.Thread):
    def __init__(self, threadID, name):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name
    def run(self):
        print "Starting " + self.name
        PlayerOperation()
        print "Exiting " + self.name

#Thread for Network Connection
class NetworkThread (threading.Thread):
    def __init__(self, threadID, name):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name
    def run(self):
        print "Starting " + self.name
        CheckInternet(10)
        print "Exiting " + self.name
		
# Create new threads
thread1 = ControlThread(1, "Control Thread")
thread2 = DisplayThread(2, "Display Thread")
thread3 = PlayerThread(3, "Player Thread")
thread4 = NetworkThread(3, "Network Connection Thread")


# Start Threads
thread4.start()
time.sleep(2)
thread1.start()
time.sleep(8)
thread2.start()
time.sleep(3)
thread3.start()