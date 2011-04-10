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

    #show progress to user
    progress = xbmcgui.DialogProgress()
    progress.create("Trakt Utilities", __language__(1162).encode( "utf-8", "ignore" )) # Retreiving information from Trakt servers
    
    options = []
    progress.update(1)
    data = getRecommendedMoviesFromTrakt()
    
    if data == None: # data = None => there was an error
        return # error already displayed in utilities.py
        
    progress.update(80,  __language__(1163).encode( "utf-8", "ignore" )) # Cross-referencing with local information
    
    i = 0;
    for movie in data:
        i+=1
        try:
            movie['idMovie'] = getMovieIdFromXBMC(movie['imdb_id'], movie['title'])
            localcopy = "   "
            if movie['idMovie'] != -1:
                localcopy = "> "
            options.append(localcopy+movie['title']+" ["+str(movie['year'])+"]")
            if progress.iscanceled():
                return
            progress.update(80+(20*i)/len(data))
        except KeyError:
            pass # Error ? skip this movie
    
    progress.close()
    
    if len(options) == 0:
        xbmcgui.Dialog().ok(__language__(1201).encode( "utf-8", "ignore" ), __language__(1158).encode( "utf-8", "ignore" )) # Trakt Utilities, 
        return
    
    while True:
        select = xbmcgui.Dialog().select(__language__(1255).encode( "utf-8", "ignore" ), options) # Recommended Movies
        Debug("Select: " + str(select))
        if select == -1:
            Debug ("menu quit by user")
            return
        
        if data[select]['idMovie'] == -1:
            xbmcgui.Dialog().ok(__language__(1201).encode( "utf-8", "ignore" ), __language__(1162).encode( "utf-8", "ignore" )) # Trakt Utilities, This movie was not found in XBMC's library
            pass
        playMovieById(data[select]['idMovie'])
    
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
