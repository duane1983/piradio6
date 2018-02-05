#!/usr/bin/env python
#
# Raspberry Pi Graphical Internet Radio
# This program interfaces with the Music Player Daemon MPD
#
# $Id: vgradio.py,v 1.56 2018/02/03 11:29:16 bob Exp $
#
# Author : Bob Rathbone
# Site   : http://www.bobrathbone.com
#
# License: GNU V3, See https://www.gnu.org/copyleft/gpl.html
#
# Disclaimer: Software is provided as is and absolutly no warranties are implied or given.
#	  The authors shall not be liable for any loss or damage however caused.

import os,sys
import locale
import pygame
import time
import pdb
import signal
from time import strftime

# Pygame controls
from pygame.locals import *
from gcontrols_class import *

# Radio imports
from log_class import Log
from radio_class import Radio
from event_class import Event
from menu_class import Menu
from message_class import Message
from graphic_display import GraphicDisplay

log = Log()
rmenu = Menu()
radio = None
radioEvent = None
message = None

# Initialise pygame
size = (800, 480)
pygame.display.init()
pygame.font.init()
myfont = pygame.font.SysFont('freesans', 20, bold=True)
screen = None

# Tuner scale range
margin = 50 	# Top bottom
lmargin = 30	# Left margin
rmargin = 80	# Right margin 

pidfile = "/var/run/radiod.pid"

playlist = []
plName = ''	# Playlist name if more than one

# Start the radio and MPD
def setupRadio(radio):
	global message,display
	log.message("Starting graphic radio ", log.INFO)

	radio.start()	      # Start it
	radio.loadSource()	    # Load sources and playlists

	display.setSize(size)
	message = Message(radio,display)
	return

# Return the page that this station is to be displayed on
def getPage(currentID,maxStations):
	page = int(currentID/maxStations)
	if currentID % maxStations == 0 and page > 0:
			   page -= 1
	return page

# Get the maximum stations labels to be displayed per page
def getMaximumLabels(display,radio): 
	maxLabels = display.config.getMaximumStations()
	plsize = radio.getPlayListLength()
	currentID = radio.getCurrentID()
	page = getPage(currentID,maxLabels)
	last_page = page + 1
	#pdb.set_trace()
	if plsize < maxLabels * last_page:
		maxLabels = plsize - maxLabels * page  
	return maxLabels

# Draw the radio/media display window
def drawTunerSlider(tunerSlider,screen,display,currentID):
	maxLabels = getMaximumLabels(display,radio)
	range = size[0] - lmargin - rmargin
	xPos = int(range * currentID / maxLabels) + lmargin
	yPos = margin + 12
	width = 5
	ySize = size[1]-(2*margin)-12
	border = 0
	color = getColor(display.config.getSliderColor())
	bcolor = color
	tunerSlider.draw(screen,color,bcolor,xPos,yPos,width,ySize,border)
	return 

# Draw the radio/media display window
def drawVolumeScale(volumeScale,screen,volume):
	xPos = lmargin
	yPos = size[1] - margin
	xSize = size[0] - lmargin - rmargin
	ySize = size[1] - margin * 2
	volumeScale.draw(screen,xPos,yPos,xSize,ySize)
	return 

# Check that the label colour is valid
def getColor(lcolor):
	try:
		color = pygame.Color(lcolor)
	except:
		color = (255,255,255)
	return color

# Handle radio event
def handleEvent(radio,radioEvent):
	global artwork_file
	artwork_file = ''
	event_type = radioEvent.getType()
	source_type = radio.getSourceType()
	msg = "radioEvent.detected " + str(event_type) + ' ' + radioEvent.getName()
	log.message(msg, log.DEBUG)

	if event_type == radioEvent.SHUTDOWN:
		radio.stop()
		print "doShutdown", radio.config.doShutdown()
		if radio.config.doShutdown():
			radio.shutdown() # Shutdown the system
		else:
			sys.exit(0)

	elif event_type == radioEvent.CHANNEL_UP:
		radio.channelUp()

	elif event_type == radioEvent.CHANNEL_DOWN:
		radio.channelDown()

	elif event_type == radioEvent.VOLUME_UP:
		radio.increaseVolume()

	elif event_type == radioEvent.VOLUME_DOWN:
		radio.decreaseVolume()

	elif event_type == radioEvent.MUTE_BUTTON_DOWN:
		if radio.muted():
			radio.unmute()
		else:
			radio.mute()

	elif event_type == radioEvent.MPD_CLIENT_CHANGE:
		log.message("radioEvent Client Change",log.DEBUG)
		if source_type == radio.source.MEDIA:
			artwork_file = getArtWork(radio)

	elif event_type == radioEvent.LOAD_RADIO or event_type == radioEvent.LOAD_MEDIA \
			   or event_type == radioEvent.LOAD_AIRPLAY:
		handleSourceChange(radioEvent,radio,message)

	radioEvent.clear()
	return

# Handle keyboard key event See https://www.pygame.org/docs/ref/key.html
def handleKeyEvent(key,display,radio,radioEvent):
	if key == K_DOWN:
		radioEvent.set(radioEvent.CHANNEL_DOWN)

	elif key == K_UP:
		radioEvent.set(radioEvent.CHANNEL_UP)

	elif key == K_LEFT:
		radioEvent.set(radioEvent.VOLUME_DOWN)

	elif key == K_RIGHT:
		radioEvent.set(radioEvent.VOLUME_UP)

	elif key == K_PAGEUP:
		pageUp(display,radio)

	elif key == K_PAGEDOWN:
		pageDown(display,radio)

	elif key == K_ESCAPE:
		radio.stop()
		quit()

	elif event.key == K_q:
		mods = pygame.key.get_mods()
		if mods & pygame.KMOD_CTRL:
			radioEvent.set(radioEvent.SHUTDOWN)
	return key

# Calculate the ID from the clicked scale position
def calculateID(radio,listIndex):
	pos = pygame.mouse.get_pos()
	mPos = pos[0] - lmargin 
	range = size[0] - lmargin - rmargin
	maxLabels = getMaximumLabels(display,radio)
	newID = int(maxLabels * mPos/range) + 1
	if newID < 1:
		newID = 1
	elif newID > maxLabels:
		newID = maxLabels	
	return newID + listIndex

# This routine displays the title or bit rate
def displayTimeDate(screen,radio,message):
	dateFormat = radio.config.getGraphicDateFormat()
	timedate = strftime(dateFormat)
	banner_color_name = display.config.getBannerColor()
	try:
		color = pygame.Color(banner_color_name)
	except:
		color = pygame.Color('white')
	font = pygame.font.SysFont('freesans', 16, bold=False)
	fontSize = font.size(timedate)
	xPos = int((size[0] - fontSize[0])/2)
	yPos = 10
	textsurface = font.render(timedate, False, (color))
	screen.blit(textsurface,(xPos,yPos))
	return

# Display currently playing radio station 
def displayTitle(screen,radio,plsize):
	title = radio.getCurrentTitle()
	if len(title) < 1:
		current_id = radio.getCurrentID()
		bitrate = radio.getBitRate()
		title = "Station %s/%s: Bitrate %sk" % (current_id,plsize,bitrate)
	else:
		title = title[0:80]
		
	font = pygame.font.SysFont('freesans', 12, bold=False)
	fontSize = font.size(title)
	xPos = int((size[0] - fontSize[0])/2)
	yPos = size[1] - 20
	color = pygame.Color('white')
	textsurface = font.render(title, False, (color))
	screen.blit(textsurface,(xPos,yPos))
	return

# Display playlist name if more than one
def displayPlaylistName(screen,plName):
	if len(plName) > 0:
		plName = plName.replace('_',' ')
		plName = plName.lstrip()
		font = pygame.font.SysFont('freesans', 12, bold=False)
		xPos = 10
		yPos = 13
		color = pygame.Color('white')
		textsurface = font.render(plName, False, (color))
		screen.blit(textsurface,(xPos,yPos))
	return

# Display page number and total
def displayPagePosition(page,maxStations,plsize):
	try:
		nPages = int(plsize/maxStations) + 1
		page = page + 1
	except:
		nPages = 0
		page = 0
	font = pygame.font.SysFont('freesans', 15, bold=False)
	xPos = size[0] - int(margin * 1.1)
	yPos = size[1] - int(margin * 1.5)
	color = pygame.Color('white')
	text = str(page) + '/' + str(nPages)
	textsurface = font.render(text, False, (color))
	screen.blit(textsurface,(xPos,yPos))
	return

# Display message popup
def displayPopup(screen,radio,text):
	displayPopup = TextRectangle(pygame) 	# Text window
	font = pygame.font.SysFont('freesans', 30, bold=True)
	fx,fy = font.size(text + "A")
	xPos = int((size[0]/2) - (fx/2))
	yPos = size[1]/2
	xSize = fx
	ySize = fy
	color = (50,50,50)
	bcolor = (255,255,255)
	border = 4
	displayPopup.draw(screen,color,bcolor,xPos,yPos,xSize,ySize,border)
	line = 1 	# Not used but required
	color = (255,255,255)
	displayPopup.drawText(screen,font,color,line,text)
	return

# Display the radio station name
def displayStationName(screen,radio):
	text = radio.getSearchName()[0:40]
	font = pygame.font.SysFont('freesans', 20, bold=True)

	displayRect = TextRectangle(pygame) 	# Blank out background
	displayWindow = TextRectangle(pygame) 	# Text window
	color = (0,0,0)
	bcolor = (0,0,0)
	height = 28
	leng = len(text)
	fx,fy = font.size(text + "A")
	width = fx
	xPos = int((size[0]/2) - (width/2))
	yPos = 37
	xSize = width
	ySize = height
	border = 0
	displayRect.draw(screen,color,bcolor,xPos,yPos-5,xSize,ySize,border)
	displayWindow.draw(screen,color,bcolor,xPos,yPos,xSize,ySize,border)

	line = 1 	# Not used but required
	color = (255,230,153)
	displayWindow.drawText(screen,font,color,line,text)
	return displayWindow

# Display the station names on the scale 
def drawScaleNames(screen,radio,playlist,index,maxLabels,lmargin):
	lines = float(6)
	chars_per_line = float(110)
	maxLabels = float(maxLabels)
	try:
		tSize = int(chars_per_line/float(maxLabels/lines))
	except:
		tSize = 30
	clip =  screen.get_clip()
	font = pygame.font.SysFont('freesans', 11, bold=False)
	color = getColor(display.config.getScaleLabelsColor())
	plsize = len(playlist)
	range = size[0] - lmargin - rmargin
	xInc= int(range / maxLabels)
	firstLine = 75
	yInc = 57
	xPos = 25
	yPos = firstLine 
	screen.set_clip(xPos,0,size[0]-rmargin,size[1])
	x = 0
	lineInc = 1
	while x < maxLabels:
		try:
			text = playlist[index]
		except:
			break
		text = text[0:tSize]
		textsurface = font.render(text, False, (color))
		line = (xPos,yPos)
		screen.blit(textsurface,line)
		index += 1
		x += 1
		lineInc += 1
		if lineInc > 6:
			yPos = firstLine
			lineInc = 1
		else:
			yPos += yInc
		xPos += xInc

	# Restore original surface
	screen.set_clip(clip)
	return

# Display left arrow (Position on first station/track)
def drawLeftArrow(display,screen,LeftArrow):
	mysize = (30,30)
	xPos = 15
	yPos = 32
	myPos = (xPos,yPos)
	path = "images/arrow_left_double.png"
	LeftArrow.draw(screen,path,(myPos),(mysize))
	return

# Display right arrow (Position on first station/track)
def drawRightArrow(display,screen,RightArrow):
	mysize = (30,30)
	xPos = 755
	yPos = 32
	myPos = (xPos,yPos)
	dir = os.path.dirname(__file__)
	path = "images/arrow_right_double.png"
	RightArrow.draw(screen,path,(myPos),(mysize))
	return


# Draw Up Icon
def drawUpIcon(display,screen,upIcon):
	xPos = size[0]-margin
	yPos = 80
	#upIcon.draw(screen,xPos,yPos,path="images/Up-arrow-circle.png")
	upIcon.draw(screen,xPos,yPos)
	return

# Draw Down Icon
def drawDownIcon(display,screen,downIcon):
	xPos = size[0]-margin
	yPos = size[1] - 120
	#downIcon.draw(screen,xPos,yPos,path="images/Down-arrow-circle.png")
	downIcon.draw(screen,xPos,yPos)
	return

# Page up through playlist
def pageUp(display,radio):
	global playlist,plName
	currentID = radio.getCurrentID()
	plsize = radio.getPlayListLength()
	maxLabels = display.config.getMaximumStations()
	page = getPage(currentID,maxLabels)
	newID = ((page + 1) * maxLabels) + 1 
	
	# Cycle through playlist
	if newID > plsize:
		plName = radio.cyclePlaylist(0)
		playlist = radio.getPlayList()
		newID = 1 
	radio.play(newID)
	return newID

# Page down through playlist
def pageDown(display,radio):
	currentID = radio.getCurrentID()
	maxLabels = display.config.getMaximumStations()
	page = getPage(currentID,maxLabels)

	# If first page go to last sation in the playlist
	if page < 1:
		newID = radio.getPlayListLength()
	else:
		newID = ((page - 1) * maxLabels) + maxLabels 
		
	radio.play(newID)
	time.sleep(0.5)
	if radio.getCurrentID() != newID:
		radio.channelDown()
	return newID

# Get pid
def getPid():
        pid = None
        if os.path.exists(pidfile):
                pf = file(pidfile,'r')
                pid = int(pf.read().strip())
        return pid

# Check if program already running
def checkPid(pidfile):
	 pid = getPid()
	 if pid != None:
		  try:
			   os.kill(pid, 0)
			   msg =  "Error: gradio or radiod already running, pid " + str(pid)
			   log.message(msg,log.ERROR)
			   print msg
			   exit()
		  except Exception as e:
			   os.remove(pidfile)
	 # Write the pidfile
	 pid = str(os.getpid())
	 pf = file(pidfile,'w')
	 pf.write(pid + '\n')
	 pf.close()
	 return pid

# Stop program if stop specified on the command line
def stop():
        pid = getPid()
        if pid != None:
                os.kill(pid, signal.SIGHUP)
        exit(0)

# Main routine
if __name__ == "__main__":

	locale.setlocale(locale.LC_ALL, '')

	# Stop command
	if len(sys.argv) > 1 and sys.argv[1] == 'stop':
		os.popen("sudo service mpd stop")
		stop()

	os.popen("systemctl stop radiod")

	# See if alraedy running
	pid = checkPid(pidfile)

	# Stop the pygame mixer as it conflicts with MPD
	pygame.mixer.quit()

	font = pygame.font.SysFont('freesans', 13)
	display = GraphicDisplay(font)

	if display.config.fullScreen():
		flags = FULLSCREEN|DOUBLEBUF
	else:
		flags = DOUBLEBUF
	screen = pygame.display.set_mode(size,flags)

	# Paint screen background (Keep at start of draw routines)
	dir = os.path.dirname(__file__)
	wallpaper = dir + '/images/scale.jpg'	  # Background wallpaper
	wcolor =(0,0,0)
	if len(wallpaper) > 1:
		pic=pygame.image.load(wallpaper)
		screen.blit(pygame.transform.scale(pic,size),(0,0))
	else:
		screen.fill(Color(wcolor))

	text = "Loading Radio Stations"
	displayPopup(screen,radio,text)
	pygame.display.flip()
	surface=pygame.Surface((size))

	# Setup radio
	log.init('radio')
	radioEvent = Event()	# Add radio event handler
	radio = Radio(rmenu,radioEvent)  # Define radio
	radio.execCommand("systemctl stop radiod")
	setupRadio(radio)
	radio.setTranslate(True)	# Switch on text translation

	# Set up window title
	version = radio.getVersion()
	caption = display.config.getWindowTitle()
	caption = caption.replace('%V',version)
	pygame.display.set_caption(caption)

	tunerSlider = TunerScaleSlider(pygame)
	currentID = radio.getCurrentID()
	drawTunerSlider(tunerSlider,screen,display,currentID)
	tunerSlider.drawScale(screen,size,lmargin,rmargin)
	
	# Create screen controls
	volume = radio.getVolume()
	volumeScale = VolumeScale(pygame)
	drawVolumeScale(volumeScale,screen,volume)
	volumeScale.drawSlider(screen,volume,lmargin)
	displayWindow = displayStationName(screen,radio)
	LeftArrow = Image(pygame)
	RightArrow = Image(pygame)
	drawLeftArrow(display,screen,LeftArrow)
	drawRightArrow(display,screen,RightArrow)
	upIcon = UpIcon(pygame)
	downIcon = DownIcon(pygame)
	drawUpIcon(display,screen,upIcon)
	drawDownIcon(display,screen,downIcon)
	MuteButton = MuteButton(pygame)
	MuteButton.draw(screen,display,(size[0]-(rmargin/2)-5,size[1]/2),
					radio.muted(), size=(35,35))

	playlist = radio.getPlayList()
	maxLabels = getMaximumLabels(display,radio)
	maxStations = display.config.getMaximumStations()
	listIndex = 0	# Playlist index
	keyPress = -1
	sliderIndex = 0

	# Start of main processing loop
	while True:
		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				radio.stop()
				quit()

			elif event.type == pygame.MOUSEBUTTONDOWN:
				radio.unmute()

				if tunerSlider.clicked(event):
					newID = calculateID(radio,listIndex)
					radio.play(newID)

				elif volumeScale.clicked(event):
					volume = volumeScale.getVolume()
					radio.setRealVolume(volume)

				elif LeftArrow.clicked():
					pageDown(display,radio)

				elif RightArrow.clicked():
					pageUp(display,radio)

				elif upIcon.clicked():
					radioEvent.set(radioEvent.CHANNEL_UP)
					
				elif downIcon.clicked():
					radioEvent.set(radioEvent.CHANNEL_DOWN)

			elif event.type == pygame.MOUSEMOTION:
				#mButton = pygame.mouse.get_pressed()[0]
				#if volumeScale.dragged(event) and mButton == 1:
				if volumeScale.dragged(event):
					volume = volumeScale.getVolume()
					radio.setRealVolume(volume)

			elif event.type == KEYDOWN:
				keyPress = handleKeyEvent(event.key,display,radio,radioEvent)

			elif MuteButton.pressed():
				if radio.muted():
					radio.unmute()
				else:
					radio.mute()
				time.sleep(0.5)

		# Handle radio events
		if radioEvent.detected():
			log.message("radioEvent.detected", log.DEBUG)
			handleEvent(radio,radioEvent)

		# These must be drawn first so that they are hidden
		tunerSlider.drawScale(screen,size,lmargin,rmargin)
		volume = radio.getVolume()
		drawVolumeScale(volumeScale,screen,volume)
		
		# Paint screen background (Keep at start of draw routine)
		pic = pygame.image.load(wallpaper)
		screen.blit(pygame.transform.scale(pic,size),(0,0))

		# Display the radio details
		if display.config.displayDate():
			displayTimeDate(screen,radio,message)

		displayPlaylistName(screen,plName)

		# Scrolling station names
		currentID = radio.getCurrentID()
		page = getPage(currentID,maxStations)
		maxLabels =  getMaximumLabels(display,radio) 
		sliderIndex = (currentID -  maxStations * page) - 1
		listIndex = (page * maxStations)

		drawTunerSlider(tunerSlider,screen,display,sliderIndex)
		drawScaleNames(screen,radio,playlist,listIndex,maxLabels,lmargin)

		displayStationName(screen,radio)
		drawLeftArrow(display,screen,LeftArrow)
		drawRightArrow(display,screen,RightArrow)
		drawUpIcon(display,screen,upIcon)
		drawDownIcon(display,screen,downIcon)

		volumeScale.drawSlider(screen,volume,lmargin)
		MuteButton.draw(screen,display,(size[0]-(rmargin/2)-7,(size[1]/2)-18),
						radio.muted(), size=(35,35))

		# Display title and page position
		plsize = len(playlist)
		if display.config.displayTitle():
			displayTitle(screen,radio,plsize)
		displayPagePosition(page,maxStations,plsize)
		pygame.display.flip()

	# End of main while loop

# End of program
