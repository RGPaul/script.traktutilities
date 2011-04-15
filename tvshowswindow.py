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
YEAR = 107
RUNTIME = 108
TAGLINE = 109
TVSHOW_LIST = 110
RATING = 111
WATCHERS = 112

#get actioncodes from keymap.xml
ACTION_PREVIOUS_MENU = 10
ACTION_SELECT_ITEM = 7

class TVShowsWindow(xbmcgui.WindowXML):

    tvshows = None

    def initWindow(self, tvshows):
        self.tvshows = tvshows
        
    def onInit(self):
        if self.tvshows != None:
            for tvshow in self.tvshows:
                self.getControl(TVSHOW_LIST).addItem(xbmcgui.ListItem(tvshow['title'], '', tvshow['images']['poster']))
            self.setFocus(self.getControl(TVSHOW_LIST))
            self.listUpdate()
        
    def onFocus( self, controlId ):
    	self.controlId = controlId
        
    def listUpdate(self):
        from utilities import Debug
        
        try:
            current = self.getControl(TVSHOW_LIST).getSelectedPosition()
        except TypeError:
            return # ToDo: error output
        
        try:
            self.getControl(BACKGROUND).setImage(self.tvshows[current]['images']['fanart'])
        except KeyError:
            Debug("KeyError for Backround")
        except TypeError:
            Debug("TypeError for Backround")
        try:
            self.getControl(TITLE).setLabel(self.tvshows[current]['title'])
        except KeyError:
            Debug("KeyError for Title")
            self.getControl(TITLE).setLabel("")
        except TypeError:
            Debug("TypeError for Title")
        try:
            self.getControl(OVERVIEW).setText(self.tvshows[current]['overview'])
        except KeyError:
            Debug("KeyError for Overview")
            self.getControl(OVERVIEW).setText("")
        except TypeError:
            Debug("TypeError for Overview")
        try:
            self.getControl(YEAR).setLabel("Year: " + str(self.tvshows[current]['year']))
        except KeyError:
            Debug("KeyError for Year")
            self.getControl(YEAR).setLabel("")
        except TypeError:
            Debug("TypeError for Year")
        try:
            self.getControl(RUNTIME).setLabel("Runtime: " + str(self.tvshows[current]['runtime']) + " Minutes")
        except KeyError:
            Debug("KeyError for Runtime")
            self.getControl(RUNTIME).setLabel("")
        except TypeError:
            Debug("TypeError for Runtime")
        try:
            self.getControl(TAGLINE).setLabel(self.tvshows[current]['tagline'])
        except KeyError:
            Debug("KeyError for Tagline")
            self.getControl(TAGLINE).setLabel("")
        except TypeError:
            Debug("TypeError for Tagline")
        try:
            self.getControl(RATING).setLabel("Rating: " + self.tvshows[current]['certification'])
        except KeyError:
            Debug("KeyError for Rating")
            self.getControl(RATING).setLabel("")
        except TypeError:
            Debug("TypeError for Rating")
        try:
            self.getControl(WATCHERS).setLabel(str(self.tvshows[current]['watchers']) + " people watching")
        except KeyError:
            Debug("KeyError for Watchers")
            self.getControl(WATCHERS).setLabel("")
        except TypeError:
            Debug("TypeError for Watchers")


    def onAction(self, action):
        from utilities import Debug

        if action == ACTION_PREVIOUS_MENU:
            Debug("Closing TV Shows Window")
            self.close()
        elif action.getId() in (1,2,107):
            self.listUpdate()
        elif action.getId() == ACTION_SELECT_ITEM:
            pass # do something here ?

