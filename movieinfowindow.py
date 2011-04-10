# -*- coding: utf-8 -*-
# @author Ralph-Gordon Paul
# 

import xbmc,xbmcaddon,xbmcgui
from utilities import *

__settings__ = xbmcaddon.Addon( "script.TraktUtilities" )
__language__ = __settings__.getLocalizedString

MOVIE_TITLE = 3
MOVIE_OVERVIEW = 4
MOVIE_POSTER = 5
PLAY_BUTTON = 6

#get actioncodes from keymap.xml
ACTION_PREVIOUS_MENU = 10
ACTION_SELECT_ITEM = 7

class MovieInfoWindow(xbmcgui.Window):

    def __init__(self):
        self.setCoordinateResolution(0) # 1920x1080
        self.background = xbmcgui.ControlImage(0, 0, 1920, 1080, '', aspectRatio=2)
        self.addControl(self.background)
        self.title = xbmcgui.ControlLabel(0, 30, 1920, 80, '', font='font13', textColor='0xFFFFFFFF', alignment=2)
        self.addControl(self.title)
        self.overview = xbmcgui.ControlTextBox(600, 200, 1300, 435, 'font13', '0xFFFFFFFF')
        self.addControl(self.overview)
        self.poster = xbmcgui.ControlImage(30, 30, 400, 600, '', aspectRatio=2)
        self.addControl(self.poster)
        self.year = xbmcgui.ControlLabel(30, 800, 1920, 40, '', font='font13', textColor='0xFFFFFFFF', alignment=0)
        self.addControl(self.year)
        self.runtime = xbmcgui.ControlLabel(30, 840, 1920, 40, '', font='font13', textColor='0xFFFFFFFF', alignment=0)
        self.addControl(self.runtime)
        self.playButton = xbmcgui.ControlButton(1000, 900, 100, 50, 'Play', font='font13', textColor='0xFFFFFFFF', shadowColor='0xFF000000', alignment=2)
        self.addControl(self.playButton)
        self.setFocus(self.playButton)
    
    def initWindow(self, movie):
        self.movie = movie
        self.title.setLabel(movie['title'])
        self.overview.setText(self.movie['overview'])
        self.poster.setImage(movie['images']['poster'])
        self.background.setImage(movie['images']['fanart'])
        self.year.setLabel("Year: " + str(movie['year']))
        self.runtime.setLabel("Runtime: " + str(movie['runtime']) + " Minutes")
        
    def onFocus( self, controlId ):
    	self.controlId = controlId
        
    def onControl(self, control):
        if control == self.playButton:
            print "Trakt Utilities: pressed Play"

    def onAction(self, action):
        buttonCode =  action.getButtonCode()
        actionID   =  action.getId()
        print "Trakt Utilities: actionID: " + str(actionID) + " buttonCode: " + str(buttonCode)
        
        if action == ACTION_PREVIOUS_MENU:
            print "Trakt Utilities: Closing MovieInfoWindow"
            self.close()

