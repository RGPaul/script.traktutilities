# -*- coding: utf-8 -*-
# @author Ralph-Gordon Paul
# 

import os
import xbmc,xbmcaddon,xbmcgui
import time, socket
import simplejson as json
from utilities import *

try:
    # Python 3.0 +
    import http.client as httplib
except ImportError:
    # Python 2.7 and earlier
    import httplib

try:
  # Python 2.6 +
  from hashlib import sha as sha
except ImportError:
  # Python 2.5 and earlier
  import sha
  
try:
    # Python 2.4
    import pysqlite2.dbapi2 as sqlite3
except:
    # Python 2.6 +
    import sqlite3 

# read settings
__settings__ = xbmcaddon.Addon( "script.TraktUtilities" )
__language__ = __settings__.getLocalizedString

apikey = '0a698a20b222d0b8637298f6920bf03a'
username = __settings__.getSetting("username")
pwd = sha.new(__settings__.getSetting("password")).hexdigest()
debug = __settings__.getSetting( "debug" )

conn = httplib.HTTPConnection('api.trakt.tv')
headers = {"Content-type": "application/x-www-form-urlencoded", "Accept": "text/plain"}

BACKGROUND = 102
TITLE = 103
OVERVIEW = 104
POSTER = 105
YEAR = 107
RUNTIME = 108
TAGLINE = 109
MOVIE_LIST = 110
RATING = 111

#get actioncodes from keymap.xml
ACTION_PREVIOUS_MENU = 10
ACTION_SELECT_ITEM = 7

# list watchlist movies
def showWatchlistMovies():
    
    options = []
    movies = getWatchlistMoviesFromTrakt()
    
    if movies == None: # data = None => there was an error
        return # error already displayed in utilities.py
    
    if len(movies) == 0:
        xbmcgui.Dialog().ok(__language__(1201).encode( "utf-8", "ignore" ), __language__(1160).encode( "utf-8", "ignore" )) # Trakt Utilities, there are no movies in your watchlist
        return
        
    # display watchlist movie list
    ui = WatchlistMovieWindow("watchlist-movies.xml", __settings__.getAddonInfo('path'), "Default")
    ui.initWindow(movies)
    ui.doModal()
    del ui

# @author Ralph-Gordon Paul, Adrian Cowan (othrayte)
class WatchlistMovieWindow(xbmcgui.WindowXML):

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
        except TypeError:
            Debug("TypeError for Title")
        try:
            self.getControl(OVERVIEW).setText(self.movies[current]['overview'])
        except KeyError:
            Debug("KeyError for Overview")
        except TypeError:
            Debug("TypeError for Overview")
        try:
            self.getControl(YEAR).setLabel("Year: " + str(self.movies[current]['year']))
        except KeyError:
            Debug("KeyError for Year")
        except TypeError:
            Debug("TypeError for Year")
        try:
            self.getControl(RUNTIME).setLabel("Runtime: " + str(self.movies[current]['runtime']) + " Minutes")
        except KeyError:
            Debug("KeyError for Runtime")
        except TypeError:
            Debug("TypeError for Runtime")
        try:
            self.getControl(TAGLINE).setLabel(self.movies[current]['tagline'])
        except KeyError:
            Debug("KeyError for Tagline")
        except TypeError:
            Debug("TypeError for Tagline")
        try:
            self.getControl(RATING).setLabel("Rating: " + self.movies[current]['certification'])
        except KeyError:
            Debug("KeyError for Rating")
        except TypeError:
            Debug("TypeError for Rating")
        
    def onFocus( self, controlId ):
    	self.controlId = controlId

    def onAction(self, action):
        from utilities import Debug
        
        if action == ACTION_PREVIOUS_MENU:
            Debug("Closing WatchlistMovieWindow")
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

# list watchlist tv shows
def showWatchlistTVShows():

    tvshows = getWatchlistTVShowsFromTrakt()
    
    if tvshows == None: # tvshows = None => there was an error
        return # error already displayed in utilities.py
    
    if len(tvshows) == 0:
        xbmcgui.Dialog().ok(__language__(1201).encode( "utf-8", "ignore" ), __language__(1161).encode( "utf-8", "ignore" )) # Trakt Utilities, there are no tv shows in your watchlist
        return
    
    # display watchlist tv shows
    import tvshowswindow
    ui = tvshowswindow.TVShowsWindow("tvshows.xml", __settings__.getAddonInfo('path'), "Default")
    ui.initWindow(tvshows)
    ui.doModal()
    del ui
    
