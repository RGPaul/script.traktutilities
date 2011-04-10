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

# list watchlist movies
def showWatchlistMovies():
    
    options = []
    data = getWatchlistMoviesFromTrakt()
    
    if data == None: # data = None => there was an error
        return # error already displayed in utilities.py

    for movie in data:
        try:
            options.append(movie['title']+" ["+str(movie['year'])+"]")
        except KeyError:
            pass # Error ? skip this movie
            
    if len(options) == 0:
        xbmcgui.Dialog().ok(__language__(1201).encode( "utf-8", "ignore" ), __language__(1160).encode( "utf-8", "ignore" )) # Trakt Utilities, there are no movies in your watchlist
        return
    
    while True:
        select = xbmcgui.Dialog().select(__language__(1252).encode( "utf-8", "ignore" ), options) # Watchlist Movies
        Debug("Select: " + str(select))
        if select == -1:
            Debug ("menu quit by user")
            return
		
        playMovieById(getMovieIdFromXBMC(data[select]['imdb_id'], data[select]['title']))
        
        """
        movie = data[select]
        
        title_label = xbmcgui.ControlLabel(100, 250, 75, movie['title'], angle=45)
        movie_window = xbmcgui.Window(10000)
        movie_window.addControl(title_label)
        
        movie_window.doModal()
        """

# list watchlist tv shows
def showWatchlistTVShows():

    options = []
    data = getWatchlistTVShowsFromTrakt()

    for tvshow in data:
        try:
            options.append(tvshow['title'])
        except KeyError:
            pass # Error ? skip this movie
    
    if len(options) == 0:
        xbmcgui.Dialog().ok(__language__(1201).encode( "utf-8", "ignore" ), __language__(1161).encode( "utf-8", "ignore" )) # Trakt Utilities, there are no tv shows in your watchlist
        return
    
    while True:
        select = xbmcgui.Dialog().select(__language__(1252).encode( "utf-8", "ignore" ), options) # Watchlist Movies
        Debug("Select: " + str(select))
        if select == -1:
            Debug ("menu quit by user")
            return
        
        xbmcgui.Dialog().ok(__language__(1201).encode( "utf-8", "ignore" ), __language__(1157).encode( "utf-8", "ignore" )) # Trakt Utilities, comming soon
    
