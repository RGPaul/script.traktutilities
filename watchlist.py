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
    
    movies = getWatchlistMoviesFromTrakt()
    
    if movies == None: # movies = None => there was an error
        return # error already displayed in utilities.py
    
    if len(movies) == 0:
        xbmcgui.Dialog().ok(__language__(1201).encode( "utf-8", "ignore" ), __language__(1160).encode( "utf-8", "ignore" )) # Trakt Utilities, there are no movies in your watchlist
        return
        
    # display watchlist movie list
    import movieswindow
    ui = movieswindow.MoviesWindow("movies.xml", __settings__.getAddonInfo('path'), "Default")
    ui.initWindow(movies)
    ui.doModal()
    del ui

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
    
