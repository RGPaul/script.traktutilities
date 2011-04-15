# -*- coding: utf-8 -*-
# @author Ralph-Gordon Paul
# 

import xbmc,xbmcaddon,xbmcgui
from utilities import *

# read settings
__settings__ = xbmcaddon.Addon( "script.TraktUtilities" )
__language__ = __settings__.getLocalizedString

BACKGROUND = 102
TITLE = 103
OVERVIEW = 104
POSTER = 105
YEAR = 107
RUNTIME = 108
TAGLINE = 109
MOVIE_LIST = 110
RATING = 111
WATCHERS = 112

#get actioncodes from keymap.xml
ACTION_PREVIOUS_MENU = 10
ACTION_SELECT_ITEM = 7

# @author Ralph-Gordon Paul, Adrian Cowan (othrayte)
class MoviesWindow(xbmcgui.WindowXML):

    movies = None

    def initWindow(self, movies):
        self.movies = movies
        
    def onInit(self):
        from utilities import Debug
        if self.movies != None:
            for movie in self.movies:
                self.getControl(MOVIE_LIST).addItem(xbmcgui.ListItem(movie['title'], '', movie['images']['poster']))
            self.setFocus(self.getControl(MOVIE_LIST))
            self.listUpdate()
        else:
            Debug("MoviesWindow: Error: movies array is empty")
            self.close()

    def listUpdate(self):
        from utilities import Debug
        try:
            current = self.getControl(MOVIE_LIST).getSelectedPosition()
        except TypeError:
            return # ToDo: error output
        
        try:
            self.getControl(BACKGROUND).setImage(self.movies[current]['images']['fanart'])
        except KeyError:
            Debug("KeyError for Backround")
        except TypeError:
            Debug("TypeError for Backround")
        try:
            self.getControl(TITLE).setLabel(self.movies[current]['title'])
        except KeyError:
            Debug("KeyError for Title")
            self.getControl(TITLE).setLabel("")
        except TypeError:
            Debug("TypeError for Title")
        try:
            self.getControl(OVERVIEW).setText(self.movies[current]['overview'])
        except KeyError:
            Debug("KeyError for Overview")
            self.getControl(OVERVIEW).setText("")
        except TypeError:
            Debug("TypeError for Overview")
        try:
            self.getControl(YEAR).setLabel("Year: " + str(self.movies[current]['year']))
        except KeyError:
            Debug("KeyError for Year")
            self.getControl(YEAR).setLabel("")
        except TypeError:
            Debug("TypeError for Year")
        try:
            self.getControl(RUNTIME).setLabel("Runtime: " + str(self.movies[current]['runtime']) + " Minutes")
        except KeyError:
            Debug("KeyError for Runtime")
            self.getControl(RUNTIME).setLabel("")
        except TypeError:
            Debug("TypeError for Runtime")
        try:
            self.getControl(TAGLINE).setLabel(self.movies[current]['tagline'])
        except KeyError:
            Debug("KeyError for Tagline")
            self.getControl(TAGLINE).setLabel("")
        except TypeError:
            Debug("TypeError for Tagline")
        try:
            self.getControl(RATING).setLabel("Rating: " + self.movies[current]['certification'])
        except KeyError:
            Debug("KeyError for Rating")
            self.getControl(RATING).setLabel("")
        except TypeError:
            Debug("TypeError for Rating")
        try:
            self.getControl(WATCHERS).setLabel(str(self.movies[current]['watchers']) + " people watching")
        except KeyError:
            Debug("KeyError for Watchers")
            self.getControl(WATCHERS).setLabel("")
        except TypeError:
            Debug("TypeError for Watchers")
        
    def onFocus( self, controlId ):
    	self.controlId = controlId

    def onAction(self, action):
        from utilities import Debug
        
        if action == ACTION_PREVIOUS_MENU:
            Debug("Closing MoviesWindow")
            self.close()
        elif action.getId() in (1,2,107):
            self.listUpdate()
        elif action.getId() == ACTION_SELECT_ITEM:
            movie = self.movies[self.getControl(MOVIE_LIST).getSelectedPosition()]
            movie_id = getMovieIdFromXBMC(movie['imdb_id'], movie['title'])
            if movie_id == -1: # Error
                xbmcgui.Dialog().ok("Trakt Utilities", movie['title'].encode( "utf-8", "ignore" ) + " " + __language__(1162).encode( "utf-8", "ignore" )) # "moviename" not found in your XBMC Library
            else:
                playMovieById(movie_id)

