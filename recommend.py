# -*- coding: utf-8 -*-
# @author Ralph-Gordon Paul, Adrian Cowan (othrayte)
# 

import xbmc,xbmcaddon,xbmcgui
from utilities import *

# read settings
__settings__ = xbmcaddon.Addon( "script.TraktUtilities" )
__language__ = __settings__.getLocalizedString

apikey = '0a698a20b222d0b8637298f6920bf03a'
username = __settings__.getSetting("username")
pwd = sha.new(__settings__.getSetting("password")).hexdigest()
debug = __settings__.getSetting( "debug" )

conn = httplib.HTTPConnection('api.trakt.tv')
headers = {"Content-type": "application/x-www-form-urlencoded", "Accept": "text/plain"}

# list reccomended movies
def showRecommendedMovies():

    options = []
    data = getRecommendedMoviesFromTrakt()
    
    if data == None: # data = None => there was an error
        return # error already displayed in utilities.py

    for movie in data:
        try:
            options.append(movie['title']+" ["+str(movie['year'])+"]")
        except KeyError:
            pass # Error ? skip this movie
    
    if len(options) == 0:
        xbmcgui.Dialog().ok(__language__(1201).encode( "utf-8", "ignore" ), __language__(1158).encode( "utf-8", "ignore" )) # Trakt Utilities, there are no movies recommended for you
        return
    
    while True:
        select = xbmcgui.Dialog().select(__language__(1255).encode( "utf-8", "ignore" ), options) # Recommended Movies
        Debug("Select: " + str(select))
        if select == -1:
            Debug ("menu quit by user")
            return
        
        playMovieById(getMovieIdFromXBMC(data[select]['imdb_id'], data[select]['title']))
    
# list reccomended tv shows
def showRecommendedTVShows():

    options = []
    data = getRecommendedTVShowsFromTrakt()
    
    if data == None: # data = None => there was an error
        return # error already displayed in utilities.py

    for tvshow in data:
        try:
            options.append(tvshow['title'])
        except KeyError:
            pass # Error ? skip this movie
    
    if len(options) == 0:
        xbmcgui.Dialog().ok(__language__(1201).encode( "utf-8", "ignore" ), __language__(1159).encode( "utf-8", "ignore" )) # Trakt Utilities, there are no tv shows recommended for you
        return
    
    while True:
        select = xbmcgui.Dialog().select(__language__(1256).encode( "utf-8", "ignore" ), options) # Recommended Movies
        Debug("Select: " + str(select))
        if select == -1:
            Debug ("menu quit by user")
            return
        xbmcgui.Dialog().ok(__language__(1201).encode( "utf-8", "ignore" ), __language__(1157).encode( "utf-8", "ignore" )) # Trakt Utilities, comming soon
