# -*- coding: utf-8 -*-
# @author Ralph-Gordon Paul
# 

import xbmc,xbmcaddon,xbmcgui
from utilities import *

__settings__ = xbmcaddon.Addon( "script.TraktUtilities" )
__language__ = __settings__.getLocalizedString

BACKGROUND = 2
TITLE = 3
OVERVIEW = 4
POSTER = 5
PLAY_BUTTON = 6
YEAR = 7
RUNTIME = 8

#get actioncodes from keymap.xml
ACTION_PREVIOUS_MENU = 10
ACTION_SELECT_ITEM = 7

class MovieInfoWindow(xbmcgui.WindowXML):

    def initWindow(self, movie):
        self.movie = movie
        self.getControl(BACKGROUND).setImage(movie['images']['fanart'])
        self.getControl(POSTER).setImage(movie['images']['poster'])
        self.getControl(TITLE).setLabel(movie['title'])
        self.getControl(OVERVIEW).setText(self.movie['overview'])
        self.getControl(YEAR).setLabel("Year: " + str(movie['year']))
        self.getControl(RUNTIME).setLabel("Runtime: " + str(movie['runtime']) + " Minutes")
        
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

