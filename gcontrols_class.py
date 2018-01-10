#!/usr/bin/env python
#
# Raspberry Pi Internet Radio
# Graphic screen controls
#
# $Id: gcontrols_class.py,v 1.13 2018/01/07 11:22:14 bob Exp $
#
# Author : Bob Rathbone
# Site   : http://www.bobrathbone.com
#
# License: GNU V3, See https://www.gnu.org/copyleft/gpl.html
#
# Disclaimer: Software is provided as is and absolutly no warranties are implied or given.
#          The authors shall not be liable for any loss or damage however caused.
#
# This program uses the SGC widget routines written by Sam Bull
# Copyright (C) SGC widget routines 2010-2013 Sam Bull
# SGC documentation: https://program.sambull.org/sgc/sgc.widgets.html
#
import time
import sys,os
from sgc.widgets.base_widget import Simple

# Objects: Mute Button
class MuteButton:
	# Initialisation routine
	def __init__(self,pygame):
		self.pygame = pygame
		return

	def draw(self,screen,display,pos,muted):
		# Mute image
		dir = os.path.dirname(__file__)
		mute_png = dir + "/images/mute.png"
		speaker_png = dir + "/images/speaker.png"
		mute_image = self.pygame.image.load(mute_png).convert_alpha()
		speaker_image = self.pygame.image.load(speaker_png).convert_alpha()
		size = (60,60)
		if muted:
			img = self.pygame.transform.scale(mute_image,(size))
		else:
			img = self.pygame.transform.scale(speaker_image, (size))
		self.mute_button = screen.blit(img,(pos))
		return

	# Has a particular control been pressed
	def pressed(self):
		hit = False
		pos = self.pygame.mouse.get_pos()
		if self.mute_button.collidepoint(pos):
			hit = True
		return hit

# Display an image found in sub-directory images
class Image:
	# Initialisation routine
	def __init__(self,pygame):
		self.pygame = pygame
		return

	# Draw the image (path relative to current directory)
	def draw(self,screen,path,(pos),(size),currentdir=True):
		if currentdir:
			dir = os.path.dirname(__file__)
			path = dir + '/' + path	
		image = self.pygame.image.load(path).convert_alpha()
		img = self.pygame.transform.scale(image, (size))
		self.image = screen.blit(img,(pos))
		return

	# Has a the image been clicked
	def clicked(self):
		hit = False
		pos = self.pygame.mouse.get_pos()
		if self.image.collidepoint(pos):
			hit = True
		return hit

# This is the basic rectangle class used in ther other classes
class Rectangle:
	# Initialisation routine
	myrect = None
	click_index = -1
	
	def __init__(self,pygame):
		self.pygame = pygame
		return

	# Draw the rectangle with or without border
	def draw(self,screen,color,bcolor,xPos,yPos,xSize,ySize,border):
		self.xPos = xPos
		self.yPos = yPos
		self.xSize = xSize
		self.ySize = ySize
		self.color = color
		if border > 0:
			rectBorder = self.pygame.Rect(xPos-border, yPos-border,
						 xSize+border*2, ySize+border*2)
			screen.fill((bcolor),rectBorder)
		self.myrect = self.pygame.Rect(xPos,yPos, xSize, ySize)
		screen.fill((color),self.myrect)
		return 

	# Detect button down
	def clicked(self,event):
		rect_click = False
		if self.myrect.collidepoint(self.pygame.mouse.get_pos()):
			if event.type == self.pygame.MOUSEBUTTONDOWN:
				rect_click = True
		return rect_click

	# Detect button hover
	def hover(self,event):
		hover = False
		if self.myrect.collidepoint(self.pygame.mouse.get_pos()):
			hover = True
		return hover

	def dragged(self,event):
		dragged = False
		if self.myrect.collidepoint(self.pygame.mouse.get_pos()) \
					and event.type == self.pygame.MOUSEMOTION:
			dragged = True
		return dragged

	def getRect(self):
		return (self.xPos,self.yPos,self.xSize,self.ySize)

# This is the text rectangle class used in ther other classes
class TextRectangle:
	# Initialisation routine
	myrect = None
	click_index = -1
	
	def __init__(self,pygame):
		self.pygame = pygame
		return

	# Draw the rectangle with or without border
	def draw(self,screen,color,bcolor,xPos,yPos,xSize,ySize,border):
		self.myrect = Rectangle(self.pygame)
		self.myrect.draw(screen,color,bcolor,xPos,yPos,xSize,ySize,border)
		return

	# Detect button down
	def clicked(self,event):
		return self.myrect.clicked(event)

	def getRect(self):
		return self.myrect.getRect()

	def drawText(self,screen,font,color,line,text):
		textsurface = font.render(text,False,(color))
		fontSize = font.size(text)
		yFontSize = fontSize[1]
		rect = self.getRect()
		xPos = rect[0] + 6
		yPos = yFontSize * (line-1) + rect[1]

		# Clip the drawing area to current rectangle only
		clip =  screen.get_clip()
		screen.set_clip((rect))
		screen.blit(textsurface,(xPos,yPos))
		# Restore original surface
		screen.set_clip(clip)
		return

# Vertical slider (for search box)
class VerticalSlider:

	def __init__(self,pygame):
		self.pygame = pygame
		return

	# Draw the vertical slider window
	def draw(self,screen,color,bcolor, xPos,yPos,xSize,ySize,border):
		self.xPos = xPos
		self.yPos = yPos
		self.xSize = xSize
		self.ySize = ySize
		self.screen = screen
		self.rect = Rectangle(self.pygame)
		self.rect.draw(screen,color,bcolor,xPos,yPos,xSize,ySize,border)
		return self

	# Set position of slider using position and range
	def setPosition(self,position,range,scolor,lcolor):
		color = (0,125,0)
		ySize = int(self.ySize / 8)
		yMax = self.ySize - ySize
		self.position = position
		self.range = range

		if position == range:
			yPos = self.yPos + yMax
		else:
			yPos = int(self.yPos + yMax * (position-1)/range)
		color = self.pygame.Color(scolor) 	# Slider colour
		bcolor = (0,0,0)

		# Draw the slider knob
		self.knob = Rectangle(self.pygame)
		self.knob.draw(self.screen,color,bcolor,\
				self.xPos,yPos,self.xSize,ySize,1)

		# Draw labels
		color = self.pygame.Color(lcolor)
		font = self.pygame.font.SysFont('freesans', 13, bold=True)
		textsurface = font.render(str(range),False,(color))	# Range label
		self.screen.blit(textsurface,(self.xPos, self.yPos + self.ySize))
		textsurface = font.render(str(position),False,(color))	# Position label
		self.screen.blit(textsurface,(self.xPos  + 25, yPos))
		return 

	# Get position (in terms of display range) of slider 
	def getPosition(self):
		mpos = self.pygame.mouse.get_pos()
	 	yPos = mpos[1] - self.yPos 
		pos = self.range * yPos/self.ySize
		if pos < 1:
			pos = 1
		return pos

	# Return the range of the search slider
	def getRange(self):
		return self.range

	# Detect button down
	def clicked(self,event):
		isClicked = self.rect.clicked(event)
		if isClicked:
			mpos = self.pygame.mouse.get_pos()

			# Convert into a position in the range
			rpos = int(mpos[1] - self.yPos)
			ypos = int(rpos*self.range/self.ySize)
			self.index = ypos - self.position 
		return isClicked

	# Mouse dragged
	def dragged(self,event):
		return self.rect.dragged(event)

	# Get new index
	def getIndex(self):
		return self.index

# End of Vertical slider class

# Scrolling box
class ScrollBox:
	lineRects = []
	click_index = -1 # Click index
	iWidth = 20 	# Slider width

	def __init__(self,pygame):
		self.pygame = pygame
		return

	# Draw the scroll box
	def draw(self,screen,color,bcolor,lines,xPos,yPos,xSize,ySize,border):
		self.xPos = xPos
		self.yPos = yPos
		self.xSize = xSize
		self.ySize = ySize
		yLineSize = int(ySize/lines)
		self.rect = Rectangle(self.pygame)
		self.rect.draw(screen,color,bcolor,xPos,yPos,xSize,ySize,border)
		yPos2 = yPos
		self.lineRects = []
		for i in range(0,lines):
			myrect = Rectangle(self.pygame) 
			if (i % 2) == 0:
				lcolor = hilight(color,50)
			else:
				lcolor = color
			myrect.draw(screen,lcolor,bcolor, xPos,yPos2,xSize,yLineSize,0)
			self.lineRects.append(myrect)	
			yPos2 += yLineSize

		# Draw the slider on the RH side
		self.slider = VerticalSlider(self.pygame)
		xPos = self.xPos + xSize + self.iWidth/2
		xSize = self.iWidth
		border = 2
		self.slider.draw(screen,color,bcolor,xPos,yPos,xSize,ySize,border)
		return 

	# Detect button down
	def clicked(self,event):
		return self.myrect.clicked(event)

	# Detect button hover
	def hover(self,event):
		return self.myrect.hover(event)

	# Draw text 
	def drawText(self,screen,font,color,textArray):
		# Get the current clip area
		self.textLines = []
		clip =  screen.get_clip()
		for i in range(0,len(self.lineRects)):
			lineRect = self.lineRects[i]
			xPos = lineRect.myrect[0]
			yPos = lineRect.myrect[1]
			if len(textArray) > i:
				text = textArray[i]
			else:
				text = ' '
			self.textLines.append(text)
			textsurface = font.render(text,False,(color))

			# Clip the drawing area to current rectangle only
			screen.set_clip(xPos,yPos,self.xSize,self.ySize)
			screen.blit(textsurface,(xPos,yPos))
		# Restore original surface
		screen.set_clip(clip)
		return 

	# Get the text of the clicked line
	def getText(self):
		text = self.textLines[self.click_index]
		return text

	def clicked(self,event):
		clicked = False
		self.click_index = -1
		for i in range(0,len(self.lineRects)):
			lineRect = self.lineRects[i]
			if lineRect.clicked(event):
				clicked = True
				self.click_index = i
				break
		return clicked
	
	def index(self):
		return self.click_index
				

# Create SGC screen widgets
class Widgets:

	# Initialisation routine
	def __init__(self,sgc,radio,display,lcolor):
		self.radio = radio
		self.create(sgc,display,lcolor)

	# Create other widgets
	def create(self,sgc,display,label_col):

		# Widget overrides and new functions
		sgc.Button.newLabel = newLabel	# New button labels
		sgc.Radio.activate = activate	# Activate a radio button
		sgc.Simple._switch = _switch 	# Prevent widget focusing from keyboard

		source_type = self.radio.getSourceType()
		xPos = display.getColumnPos(2)

		# Create search selection box
		yPos = display.getRowPos(7.5)

		self.select_list = sgc.Radio(group="group1", label="List", active=True,
						label_col=(label_col))
		self.select_playlists = sgc.Radio(group="group1", label="Playlists",
						label_col=(label_col))
		self.select_artists = sgc.Radio(group="group1", label="Artists",
						label_col=(label_col))

		self.search_box = sgc.VBox(widgets=(self.select_list,self.select_playlists,
					self.select_artists), pos=(xPos,yPos),selection=0,
					label="Search",label_side="top",label_col=(label_col))
		self.search_box.add(order=3)

		# Scale widget
		xPos = display.getColumnPos(3)
		yPos = display.getRowPos(18.5)
		if self.radio.muted():
			sVolume = "Muted"
		else:
			sVolume = "Volume"
		self.VolumeSlider = sgc.Scale(pos=(xPos,yPos), show_value=0,
					label=sVolume, label_side="bottom",label_col=(label_col))
		self.VolumeSlider.add(order=5)

		# Sources combo box
		sources = self.radio.source.getList()
		index = 0
		xPos = display.getColumnPos(34)
		yPos = display.getRowPos(19)
		self.sourceCombo = sgc.Combo(pos=(xPos,yPos),selection=index, values=(sources),
					label="Sources", label_side="bottom",label_col=(label_col))
		self.sourceCombo.add(order=6)
		return

# Draw the search Up Icon
class UpIcon:
	# Initialisation routine
	def __init__(self,pygame):
		self.pygame = pygame

	def draw(self,screen,xPos,yPos):
		self.upIcon = Image(self.pygame)
		mysize = (40,40)
		path = "images/up_icon.png"
		self.upIcon.draw(screen,path,(xPos,yPos),(mysize))
		return
	
	def clicked(self):
		return self.upIcon.clicked()

# Draw the search Down Icon
class DownIcon(Image):
	# Initialisation routine
	def __init__(self,pygame):
		self.pygame = pygame
		pass

	def draw(self,screen,xPos,yPos):
		self.downIcon = Image(self.pygame)
		mysize = (40,40)
		path = "images/down_icon.png"
		self.downIcon.draw(screen,path,(xPos,yPos),(mysize))
		return

	def clicked(self):
		return self.downIcon.clicked()

# Draw option button (Random etc)
class OptionButton:
	active = False

	# Initialisation routine
	def __init__(self,pygame):
		self.pygame = pygame

	# Draw option button and label
	def draw(self,screen,xPos,yPos,label,lcolor):
		color = (255,255,255)
		bcolor = (0,0,0)
		border = 2
		xSize = 17
		ySize = 17
		self.screen = screen
		self.rect = Rectangle(self.pygame)
		self.rect.draw(screen,color,bcolor,xPos,yPos,xSize,ySize,border)

		# Draw active indicator
		if self.active:
			color = (0,0,200)
			xpos = xPos + 2
			ypos = yPos + 2
			xsize = xSize - 4
			ysize = ySize - 4
			self.activeRect = Rectangle(self.pygame)
			self.activeRect.draw(screen,color,bcolor,xpos,ypos,xsize,ysize,0)

		# Draw the label
		font = self.pygame.font.SysFont('freesans', 16, bold=True)
		textsurface = font.render(label,False,(self.pygame.Color(lcolor)))
		self.screen.blit(textsurface,(xPos + 25, yPos))
		return

	# Activate button
	def activate(self,true_false):
		self.active = true_false

	# Return True False if button active or not
	def isActive(self):
		return self.active

	# Was control clicked
	def clicked(self,event):
		return self.rect.clicked(event)

# End of OptionButton class

# Highlight a color
def hilight(color,amount):
	rgb = list(color)
	for i in range(0,len(rgb)):
		rgb[i] += amount
		if rgb[i] > 255:
			rgb[i] -= amount * 2
	
	newcolor = (rgb[0],rgb[1], rgb[2])
	return newcolor

# This routine is added to the button class
# To redraw the label
def newLabel(self,newlabel):
	self._settings["label"] = [newlabel]
	label = newlabel.split('\n')
	label = self._settings["label"][0].split("\n")
	f = self._settings["label_font"]
	h = f.get_ascent()
	for count, line in enumerate(label):
	    lbl = Simple(f.render(line, True, self._settings["label_col"]))
	    self._settings["label"].append(lbl)
	    y = (self.rect.h - (h * len(label)) + f.get_descent()) / 2 + \
		(h * count)
	    lbl.rect.midtop = (self.rect.w/2, y)
	self._draw()

# Prevent widgets from focussing
def _switch(self,image=None):
	self._has_focus = False
	self.image = self._images[self._image_state].copy()
	return 

# Add routine to radio button widget
def activate(self):
	self._activate()

# End of controls
