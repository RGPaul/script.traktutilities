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

def showTrendingMovies():

    #show progress to user
    progress = xbmcgui.DialogProgress()
    progress.create("Trakt Utilities", __language__(1162).encode( "utf-8", "ignore" )) # Retreiving information from Trakt servers
    
    options = []
    progress.update(1)
    data = getTrendingMoviesFromTrakt()
    
    if data == None: # data = None => there was an error
        return # error already displayed in utilities.py
    
    progress.update(80,  __language__(1163).encode( "utf-8", "ignore" )) # Cross-referencing with local information
    
    i = 0;
    for movie in data:
        i+=1
        try:
            options.append(movie['title'])
            
            if progress.iscanceled():
                return
            progress.update(80+(20*i)/len(data))
        except KeyError:
            pass # Error ? skip this movie
    
    progress.close()
    
    if len(options) == 0:
        xbmcgui.Dialog().ok("Trakt Utilities", "there are no trending movies")
        return
    
    while True:
        select = xbmcgui.Dialog().select(__language__(1250).encode( "utf-8", "ignore" ), options) # Trending Movies
        Debug("Select: " + str(select))
        if select == -1:
            Debug ("menu quit by user")
            return
        
        playMovieById(getMovieIdFromXBMC([select]['imdb_id'], data[select]['title']))

def showTrendingTVShows():

    options = []
    data = getTrendingTVShowsFromTrakt()
    
    if data == None: # data = None => there was an error
        return # error already displayed in utilities.py

    for tvshow in data:
        try:
            options.append(tvshow['title'])
        except KeyError:
            pass # Error ? skip this movie
    
    if len(options) == 0:
        xbmcgui.Dialog().ok("Trakt Utilities", "there are no trending tv shows")
        return
    
    while True:
        select = xbmcgui.Dialog().select(__language__(1251).encode( "utf-8", "ignore" ), options) # Trending Movies
        Debug("Select: " + str(select))
        if select == -1:
            Debug ("menu quit by user")
            return
        xbmcgui.Dialog().ok("Trakt Utilities", "comming soon")
