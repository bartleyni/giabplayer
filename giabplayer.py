#!/usr/bin/env python3

import time
import subprocess
import urllib2
import os
import glob
import threading
import pifacecad
import re
import pifacecommon
from pifacecad.tools.question import LCDQuestion
from VLCclient import VLCClient
from pifacecad.lcd import LCD_WIDTH

### Threaded Player GIAB Micro Player ###
### Nick Bartley 2013 ###

# GLOBALS

#Available player options
OPTIONS = [\
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

#Player Control Variables
PlayerControl = None
PlayerStatus = None
player_source = None
StatusFlag = False

#General Control Variables
LastSting = 0
SelectedMode = 0
Internet = False

class Player(object):
	def __init__(self, CAD, VLC, initial_option=0):
		
		self.current_option_index = initial_option
		self.CAD = CAD
		self.VLC = VLC
		self.number_of_options = len(OPTIONS)
		self.last_sting = 0
		self.highlighted_option_index = self.current_option_index

	@property
	def current_option(self):
		"""Returns the current mode of operation."""
		return OPTIONS[self.current_option_index][1]

	@property
	def highlighted_option_index(self):
		"""Returns the currently highlighted option."""
		return self.highlighted_option_index
	
	def menu_left(self, highlighted_option=None):
		if highlighted_option <> None:
			highlighted_option = highlighted_option - 1
			if highlighted_option < 0:
				highlighted_option = (self.number_of_options-1)
			self.highlighted_option_index = highlighted_option
			return highlighted_option
		else:
			return False
	
	def menu_right(self, highlighted_option=None):
		if highlighted_option <> None:
			highlighted_option = highlighted_option + 1
			if highlighted_option > (self.number_of_options-1):
				highlighted_option = 0
			self.highlighted_option_index = highlighted_option
			return highlighted_option
		else:
			return False
	
	def menu_load(self, highlighted_option = None):
		if highlighted_option <> None:
			self.stop()
			self.current_option_index = highlighted_option
			self.load_player()
		else:
			return False
			
	def menu_load_and_play(self, highlighted_option = None):
		if highlighted_option <> None:
			self.stop()
			self.current_option_index = highlighted_option
			self.load_player()
			self.play()
		else:
			return False
			
	def play(self):
		self.VLC.connect()
		if OPTIONS[self.current_option_index][0] == "Folder":
			self.VLC.randomon()
			self.VLC.next()
		self.VLC.play()
		self.VLC.disconnect()
	
	def stop(self):
		if OPTIONS[self.current_option_index][0] == "Sting":
			self.load_player()
		self.VLC.connect()
		self.VLC.stop()
		self.VLC.disconnect()
	
	def load_player(self):
		
		option_type = OPTIONS[self.current_option_index][0]
		option_name = OPTIONS[self.current_option_index][1]
		option_address = OPTIONS[self.current_option_index][2]

		self.VLC.connect()

		if option_type == "Stream":
			player_source = option_address
			self.VLC.clear()
			self.VLC.enqueue(player_source)
			self.VLC.loopoff()
		if option_type == "Folder":
			player_source = option_address
			self.VLC.clear()
			self.VLC.enqueue(player_source)
			self.VLC.loopon()
			self.VLC.randomon()
		if option_type == "File":
			player_source = option_address
			self.VLC.clear()
			self.VLC.enqueue(player_source)
			self.VLC.loopoff()
		if option_type == "Help":
			player_source = option_address
			self.VLC.clear()
			self.VLC.enqueue(player_source)
			self.VLC.loopon()
		if option_type == "Sting":
			sting = str(self.last_sting+1)
			option_name = "Sting: "+sting
			sting_counter = len(glob.glob1(option_address,"*.mp3"))-1
			self.last_sting = self.last_sting+1
			if self.last_Sting > sting_counter:
				self.last_sting = 0
			player_source = option_address+sting+".mp3"
			self.VLC.clear()
			self.VLC.enqueue(option_address+sting+".mp3")
			self.VLC.loopoff()
			self.VLC.randomoff()
		
		self.VLC.disconnect()
		return option_name
	
	
class Display(object):
	def __init__(self, CAD, VLC):
		
		#set up display
		CAD.lcd.blink_off()
		CAD.lcd.cursor_off()
		CAD.lcd.backlight_on()
		CAD.lcd.home()
				
		self.CAD = CAD
		self.VLC = VLC
		self.last_line_one = " "
		self.last_line_two = " "

	def update_display_line_one(self, line_one):
		if line_one <> self.last_line_one:
			self.CAD.lcd.set_cursor(0, 0)
			line_one = line_one[0:LCD_WIDTH]
			self.CAD.lcd.write(line_two.ljust(LCD_WIDTH))
			self.last_line_one = line_one

	def update_display_line_two(self, line_two):
		if line_two <> self.last_line_two:
			self.CAD.lcd.set_cursor(0, 1)
			line_two = line_two[0:LCD_WIDTH]
			self.CAD.lcd.write(line_two.ljust(LCD_WIDTH))
			self.last_line_two = line_two
			
	def start_playing_info(self):
		self.display_info = True
		playing_title = " "
		player_status = " "
		
		while self.display_info:
			self.VLC.connect()
			player_state = VLC.playing()
		
			if player_state == "0":
				player_status = "Stopped"
			else:
				player_status = "Playing"
				
			playing_title = self.VLC.title()
			self.VLC.disconnect()
			status_text = player_status.center(LCD_WIDTH-1)
			self.update_display_line_two(status_text)
			time.sleep(1.5)
			if player_state <> "0":
				title_text = playing_title.center(LCD_WIDTH-1)
				self.update_display_line_two(title_text)
			time.sleep(1)		
		
	def stop_playing_info(self):
		self.display_info = False
		
def play_button(event):
	global player
	global display
	player.play()
	display.start_playing_info()
	
def stop_button(event):
	global player
	global display
	player.stop()
	display.stop_playing_info()

def menu_button(event):
	global player
	global display
	display.stop_playing_info()
	display.update_display_line_one = "Mode:"
	display.update_display_line_two = player.current_option()

def select_button(event):
	global player
	global display
	display.stop_playing_info()
	player.menu_load(player.highlighted_option_index)
	display.update_display_line_one = player.current_option()

if __name__ == "__main__":
	
	PLAYER_PROCESS = subprocess.Popen(["/usr/bin/vlc", "-I", "dummy", "--volume", "150", "--intf", "telnet", "--lua-config", "telnet={host='0.0.0.0:4212'}"])
	cad = pifacecad.PiFaceCAD()
	PLAYER_LOCK = threading.Lock()
	vlc = VLCClient("127.0.0.1",4212,"admin",1)
	
	global display
	global player
	
	player = Player(cad, vlc)
	display = Display(cad, vlc)
	
	LISTENER.register(0, pifacecad.IODIR_FALLING_EDGE, play_button)
	LISTENER.register(1, pifacecad.IODIR_FALLING_EDGE, stop_button)
	#LISTENER.register(2, pifacecad.IODIR_FALLING_EDGE, shutdown_button)
	#LISTENER.register(3, pifacecad.IODIR_FALLING_EDGE, reboot_button)
	#LISTENER.register(4, pifacecad.IODIR_FALLING_EDGE, menu_button)
	LISTENER.register(5, pifacecad.IODIR_FALLING_EDGE, select_button)
	#LISTENER.register(6, pifacecad.IODIR_FALLING_EDGE, left_button)
	#LISTENER.register(7, pifacecad.IODIR_FALLING_EDGE, right_button)
	LISTENER.activate()
	
	display.update_display_line_one = "Mode:"
	display.update_display_line_two = player.current_option()