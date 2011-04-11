# -*- coding: utf-8 -*-
# @author Ralph-Gordon Paul
# 

import xbmc,xbmcaddon,xbmcgui

__settings__ = xbmcaddon.Addon( "script.TraktUtilities" )
__language__ = __settings__.getLocalizedString

BACKGROUND = 102
TITLE = 103
OVERVIEW = 104
POSTER = 105
PLAY_BUTTON = 106
YEAR = 107
RUNTIME = 108
TAGLINE = 109

#get actioncodes from keymap.xml
ACTION_PREVIOUS_MENU = 10
ACTION_SELECT_ITEM = 7

class MovieInfoWindow(xbmcgui.WindowXML):

    movie = None

    def initWindow(self, movie):
        self.movie = movie
        
    def onInit(self):
        from utilities import Debug
        if self.movie != None:
            try:
                self.getControl(BACKGROUND).setImage(self.movie['images']['fanart'])
            except KeyError:
                Debug("KeyError for Backround")
            except TypeError:
                Debug("TypeError for Backround")
            try:
                self.getControl(POSTER).setImage(self.movie['images']['poster'])
            except KeyError:
                Debug("KeyError for Poster")
            except TypeError:
                Debug("TypeError for Poster")
            try:
                self.getControl(TITLE).setLabel(self.movie['title'])
            except KeyError:
                Debug("KeyError for Title")
            except TypeError:
                Debug("TypeError for Title")
            try:
                self.getControl(OVERVIEW).setText(self.movie['overview'])
            except KeyError:
                Debug("KeyError for Overview")
            except TypeError:
                Debug("TypeError for Overview")
            try:
                self.getControl(YEAR).setLabel("Year: " + str(self.movie['year']))
            except KeyError:
                Debug("KeyError for Year")
            except TypeError:
                Debug("TypeError for Year")
            try:
                self.getControl(RUNTIME).setLabel("Runtime: " + str(self.movie['runtime']) + " Minutes")
            except KeyError:
                Debug("KeyError for Runtime")
            except TypeError:
                Debug("TypeError for Runtime")
            try:
                self.getControl(TAGLINE).setLabel(self.movie['tagline'])
            except KeyError:
                Debug("KeyError for Runtime")
            except TypeError:
                Debug("TypeError for Runtime")
            try:
                self.playbutton = self.getControl(PLAY_BUTTON)
                self.setFocus(self.playbutton)
            except (KeyError,TypeError):
                pass
        
    def onFocus( self, controlId ):
    	self.controlId = controlId
        
    def onClick(self, controlId):
        if controlId == PLAY_BUTTON:
            pass

    def onAction(self, action):
        from utilities import Debug
        buttonCode =  action.getButtonCode()
        actionID   =  action.getId()
        
        if action == ACTION_PREVIOUS_MENU:
            Debug("Closing MovieInfoWindow")
            self.close()

