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
from vlcclient import VLCClient
from pifacecad.lcd import LCD_WIDTH

### Threaded Player GIAB Micro Player ###
### Nick Bartley 2013 ###

# GLOBALS

#Available player options

OPTIONS = [
	{'type': "Stream",
	'name': "URB",
	'source': "http://people.bath.ac.uk/su9urb/audio/urb-hi.m3u"},
	{'type': "Stream",
	'name': "JackFM",
	'source': "http://stream1.radiomonitor.com/JackBristol-128.m3u"},
	{'type': "Folder",
	'name': "Pop House Music",
	'source': "giabplayer/PopHouse/"},
	{'type': "Folder",
	'name': "ICIA House Music",
	'source': "giabplayer/ICIAHouse/"},
	{'type': "File",
	'name': "Applause",
	'source': "giabplayer/cannedApplause.wav"},
	{'type': "File",
	'name': "Ring Out",
	'source': "giabplayer/MoneyForNothing.mp3"},
	{'type': "Sting", 
	'name': "Stings", 
	'source': "giabplayer/Stings/"},
	{'type': "Help", 
	'name': "Help", 
	'source': "giabplayer/Help.mp3"},
	{'type': "Folder", 
	'name': "USB Stick", 
	'source': "/media/usb/"},
	{'type': "Info", 
	'name': "Net Info", 
	'source': None},
	{'type': "Info", 
	'name': "Sys Info", 
	'source': None},
	]

#General Control Variables
GET_TEMP_CMD = "/opt/vc/bin/vcgencmd measure_temp"
TOTAL_MEM_CMD = "free | grep 'Mem' | awk '{print $2}'"
USED_MEM_CMD = "free | grep '\-\/+' | awk '{print $3}'"
SHUTDOWN_CMD = "sudo shutdown now"
REBOOT_CMD = "sudo shutdown -r now"

def net_info():
	ether_ip = "Disconnected"
	wifi = "Disconnected"
	ether_ip = get_my_ip("eth0")
	wifi_ip = get_my_ip("wlan0")
	
	display.update_display_line_one("E"+ether_ip)
	display.update_display_line_two("W"+wifi_ip)

def get_my_ip(interface):
    return run_cmd("ifconfig "+interface+" | grep addr: | cut -d: -f2 | cut -d\" \" -f1")[:-1]
	
def run_cmd(cmd):
	return subprocess.check_output(cmd, shell=True).decode('utf-8')

def get_my_temp():
    return run_cmd(GET_TEMP_CMD)[5:9]

def get_my_free_mem():
	total_mem = int(run_cmd(TOTAL_MEM_CMD))
	used_mem = int(run_cmd(USED_MEM_CMD))
	#total_mem = 100
	#used_mem = 50
	mem_perc = float(used_mem) / total_mem
	#mem_perc = 0.5
	return "{:.1%}".format(mem_perc)

def shutdown():
	run_cmd(SHUTDOWN_CMD)

def reboot():
	run_cmd(REBOOT_CMD)
			
class Player(object):
	def __init__(self, CAD, VLC, initial_option=0):
		
		self.current_option_index = initial_option
		self.CAD = CAD
		self.VLC = VLC
		self.number_of_options = len(OPTIONS)
		self.last_sting = 0
		self.highlighted_option_index = initial_option
		self.menu_mode = True
		
	@property
	def get_menu_mode(self):
		"""Returns the menu mode True or False."""
		return self.menu_mode
		
	@property
	def get_current_option_index(self):
		"""Returns the currentl option."""
		return self.current_option_index
		
	@property
	def current_option(self):
		"""Returns the current mode of operation."""
		return OPTIONS[self.current_option_index]
		
	@property
	def highlighted_option(self):
		"""Returns the highlighted mode of operation."""
		return OPTIONS[self.highlighted_option_index]

	@property
	def get_highlighted_option_index(self):
		"""Returns the currently highlighted option."""
		return self.highlighted_option_index
	
	@property
	def get_current_sting(self):
		"""Returns the current sting number."""
		return self.last_sting
	
	def set_menu_mode(self, mode=True):
		self.menu_mode = mode
	
	def menu_left(self):
		if self.menu_mode == True:
			highlighted_option = self.highlighted_option_index
			highlighted_option = highlighted_option - 1
			if highlighted_option < 0:
				highlighted_option = (self.number_of_options-1)
			self.highlighted_option_index = highlighted_option
			return highlighted_option
	
	def menu_right(self):
		if self.menu_mode == True:
			highlighted_option = self.highlighted_option_index
			highlighted_option = highlighted_option + 1
			if highlighted_option > (self.number_of_options-1):
				highlighted_option = 0
			self.highlighted_option_index = highlighted_option
			return highlighted_option
	
	def menu_load(self):
		if self.current_option['type'] <> "Folder":
			self.stop()
		self.current_option_index = self.highlighted_option_index
		self.load_player()
		self.menu_mode = False

	def play(self):
		if self.current_option['type'] <> "Info":
			self.VLC.connect()
			if self.current_option['type'] == "Folder":
				self.VLC.randomon()
				self.VLC.next()
			self.VLC.play()
			self.VLC.disconnect()
		
	def stop(self):
		if self.current_option['type']  == "Sting":
			self.load_player()
		self.VLC.connect()
		self.VLC.stop()
		self.VLC.disconnect()
	
	def load_player(self):
		
		option_type = self.current_option['type']
		option_name = self.current_option['name']
		option_address = self.current_option['source']

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
			if self.last_sting > sting_counter:
				self.last_sting = 0
			player_source = option_address+sting+".mp3"
			self.VLC.clear()
			self.VLC.enqueue(option_address+sting+".mp3")
			self.VLC.loopoff()
			self.VLC.randomoff()
		
		self.VLC.disconnect()
		return option_name
	
class Display(object):
	def __init__(self, CAD, VLC, LOCK):
		
		#set up display
		CAD.lcd.blink_off()
		CAD.lcd.cursor_off()
		CAD.lcd.backlight_on()
		CAD.lcd.home()
				
		self.CAD = CAD
		self.VLC = VLC
		self.LOCK = LOCK
		self.last_line_one = " "
		self.last_line_two = " "

	def update_display_line_one(self, line_one):
		self.LOCK.acquire()
		if line_one <> self.last_line_one:
			self.CAD.lcd.set_cursor(0, 0)
			line_one = line_one[0:LCD_WIDTH]
			self.CAD.lcd.write(line_one.ljust(LCD_WIDTH))
			self.last_line_one = line_one
		self.LOCK.release()
		
	def update_display_line_two(self, line_two):
		self.LOCK.acquire()
		if line_two <> self.last_line_two:
			self.CAD.lcd.set_cursor(0, 1)
			line_two = line_two[0:LCD_WIDTH]
			self.CAD.lcd.write(line_two.ljust(LCD_WIDTH))
			self.last_line_two = line_two
		self.LOCK.release()
		
	def start_playing_info(self):
		self.display_info = True
		playing_title = " "
		player_status = " "
		player_state = "0"
		
		while self.display_info:
			self.VLC.connect()
			player_state = self.VLC.playing()
			playing_title = self.VLC.title()
			self.VLC.disconnect()
		
			if player_state == "0":
				player_status = "Stopped".center(LCD_WIDTH-1)
			else:
				player_status = "Playing".center(LCD_WIDTH-1)

			time.sleep(0.5)
			self.update_display_line_two(player_status)
			time.sleep(1.0)
			
			if player_state <> "0":
				title_text = playing_title.center(LCD_WIDTH-1)
				self.update_display_line_two(title_text)
			time.sleep(1.0)
		
		self.VLC.connect()
		player_state = self.VLC.playing()
		self.VLC.disconnect()
		if player_state == "0":
			player_status = "Stopped".center(LCD_WIDTH-1)
		else:
			player_status = " "
		self.update_display_line_two(player_status)
		return
		
	def stop_playing_info(self):
		self.display_info = False
	
	def sys_info(self):
		self.LOCK.acquire()
		self.CAD.lcd.home()
		self.CAD.lcd.write_custom_bitmap(0)
		self.CAD.lcd.write(":{}C ".format(get_my_temp()))

		self.CAD.lcd.write_custom_bitmap(1)
		self.CAD.lcd.write(":{}".format(get_my_free_mem()))
		self.LOCK.release()
		
def play_button(event):
	global player
	global display
	player.set_menu_mode(False)
	if player.get_highlighted_option_index <> player.get_current_option_index:
		player.menu_load()
	player.play()
	if player.current_option['type'] <> "Sting":
		display.update_display_line_one(player.current_option['name'])
	else:
		sting = str(player.get_current_sting)
		option_name = "Sting: "+sting
		display.update_display_line_one(option_name)
	display_thread = threading.Thread(target=display.start_playing_info)
	display_thread.start()
	
def stop_button(event):
	global player
	global display
	player.stop()
	if player.current_option['type'] == "Sting":
		sting = str(player.get_current_sting)
		option_name = "Sting: "+sting
		display.update_display_line_one(option_name)
	display.stop_playing_info()

def menu_button(event):
	global player
	global display
	
	player.set_menu_mode(True)
	display.stop_playing_info()
	display.update_display_line_one("Mode:")
	display.update_display_line_two(player.highlighted_option['name'])
	
def left_button(event):
	global player
	global display
	player.menu_left()
	display.update_display_line_one("Mode:")
	display.update_display_line_two(player.highlighted_option['name'])
	
def right_button(event):
	global player
	global display
	player.menu_right()
	display.update_display_line_one("Mode:")
	display.update_display_line_two(player.highlighted_option['name'])

def select_button(event):
	global player
	global display
	if player.get_menu_mode:
		if player.highlighted_option['type'] <> "Info":	
			display.stop_playing_info()
			if player.highlighted_option['name'] <> player.current_option['name']:
				player.menu_load()
			else:
				display_thread = threading.Thread(target=display.start_playing_info)
				display_thread.start()
			if player.current_option['type'] <> "Sting":	
				display.update_display_line_one(player.current_option['name'])
			else:
				sting = str(player.get_current_sting)
				option_name = "Sting: "+sting
				display.update_display_line_one(option_name)
			display.update_display_line_two(" ")
		else:
			if player.highlighted_option['name'] == "Net Info":
				net_info()
			if player.highlighted_option['name'] == "Sys Info":
				display.sys_info()
	else:
		player.set_menu_mode(True)
		display.stop_playing_info()
		display.update_display_line_one("Mode:")
		display.update_display_line_two(player.highlighted_option['name'])
		
if __name__ == "__main__":
	
	PLAYER_PROCESS = subprocess.Popen(["/usr/bin/vlc", "-I", "dummy", "--volume", "150", "--intf", "telnet", "--lua-config", "telnet={host='0.0.0.0:4212'}"])
	cad = pifacecad.PiFaceCAD()
	display_lock = threading.Lock()
	vlc = VLCClient("127.0.0.1",4212,"admin",1)
	vlc_display = VLCClient("127.0.0.1",4212,"admin",1)
	
	temperature_symbol = pifacecad.LCDBitmap([0x4, 0x4, 0x4, 0x4, 0xe, 0xe, 0xe, 0x0])
	memory_symbol = pifacecad.LCDBitmap([0xe, 0x1f, 0xe, 0x1f, 0xe, 0x1f, 0xe, 0x0])
	cad.lcd.store_custom_bitmap(0, temperature_symbol)
	cad.lcd.store_custom_bitmap(1, memory_symbol)
	
	global display
	global player
	
	player = Player(cad, vlc)
	player.set_menu_mode(True)
	display = Display(cad, vlc_display, display_lock)
	
	LISTENER = pifacecad.SwitchEventListener(chip=cad)
	
	LISTENER.register(0, pifacecad.IODIR_FALLING_EDGE, play_button)
	LISTENER.register(1, pifacecad.IODIR_FALLING_EDGE, stop_button)
	LISTENER.register(2, pifacecad.IODIR_FALLING_EDGE, left_button)
	LISTENER.register(3, pifacecad.IODIR_FALLING_EDGE, right_button)
	LISTENER.register(4, pifacecad.IODIR_FALLING_EDGE, menu_button)
	LISTENER.register(5, pifacecad.IODIR_FALLING_EDGE, select_button)
	LISTENER.register(6, pifacecad.IODIR_FALLING_EDGE, left_button)
	LISTENER.register(7, pifacecad.IODIR_FALLING_EDGE, right_button)
	LISTENER.activate()
	
	display.update_display_line_one("GIAB Micro")
	display.update_display_line_two("Verison 3.0")
	
	time.sleep(2)
	
	display.update_display_line_one("Copyright 2013")
	display.update_display_line_two("Nick Bartley")
	
	time.sleep(2)

	display.update_display_line_one("Mode:")
	playing_text = player.current_option['name']
	display.update_display_line_two(playing_text)