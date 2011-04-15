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

    movies = getRecommendedMoviesFromTrakt()

    if movies == None: # movies = None => there was an error
        return # error already displayed in utilities.py
    
    if len(movies) == 0:
        xbmcgui.Dialog().ok(__language__(1201).encode( "utf-8", "ignore" ), __language__(1158).encode( "utf-8", "ignore" )) # Trakt Utilities, there are no movies recommended for you
        return
        
    # display recommended movies list
    import movieswindow
    ui = movieswindow.MoviesWindow("movies.xml", __settings__.getAddonInfo('path'), "Default")
    ui.initWindow(movies)
    ui.doModal()
    del ui
    
# list reccomended tv shows
def showRecommendedTVShows():

    tvshows = getRecommendedTVShowsFromTrakt()
    
    if tvshows == None: # tvshows = None => there was an error
        return # error already displayed in utilities.py
    
    if len(tvshows) == 0:
        xbmcgui.Dialog().ok(__language__(1201).encode( "utf-8", "ignore" ), __language__(1159).encode( "utf-8", "ignore" )) # Trakt Utilities, there are no tv shows recommended for you
        return
    
    # display recommended tv shows
    import tvshowswindow
    ui = tvshowswindow.TVShowsWindow("tvshows.xml", __settings__.getAddonInfo('path'), "Default")
    ui.initWindow(tvshows)
    ui.doModal()
    del ui
    
