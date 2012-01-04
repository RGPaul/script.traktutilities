# -*- coding: utf-8 -*-
# 

import os
import xbmc,xbmcaddon,xbmcgui
import time, socket

try: import simplejson as json
except ImportError: import json

from utilities import *
from trakt_cache import *

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

__author__ = "Ralph-Gordon Paul, Adrian Cowan"
__credits__ = ["Ralph-Gordon Paul", "Adrian Cowan", "Justin Nemeth",  "Sean Rudford"]
__license__ = "GPL"
__maintainer__ = "Ralph-Gordon Paul"
__email__ = "ralph-gordon.paul@uni-duesseldorf.de"
__status__ = "Production"

# read settings
__settings__ = xbmcaddon.Addon( "script.TraktUtilities" )
__language__ = __settings__.getLocalizedString

apikey = '48dfcb4813134da82152984e8c4f329bc8b8b46a'
username = __settings__.getSetting("username")
pwd = sha.new(__settings__.getSetting("password")).hexdigest()
debug = __settings__.getSetting( "debug" )

conn = httplib.HTTPConnection('api.trakt.tv')
headers = {"Content-type": "application/x-www-form-urlencoded", "Accept": "text/plain"}

class Viewer():
    # list watchlist movies
    @staticmethod
    def watchlistMovies():
        
        movies = getMovieWatchlist()
        
        if movies == None: # movies = None => there was an error
            return # error already displayed in utilities.py
        
        if len(movies) == 0:
            xbmcgui.Dialog().ok(__language__(1201).encode( "utf-8", "ignore" ), __language__(1160).encode( "utf-8", "ignore" )) # Trakt Utilities, there are no movies in your watchlist
            return
            
        # display watchlist movie list
        import windows
        ui = windows.MoviesWindow("movies.xml", __settings__.getAddonInfo('path'), "Default")
        ui.initWindow(movies, 'watchlist')
        ui.doModal()
        del ui

    # list watchlist tv shows
    @staticmethod
    def watchlistShows():

        tvshows = getShowWatchlist()
        if tvshows == None: # tvshows = None => there was an error
            return # error already displayed in utilities.py
        
        if len(tvshows) == 0:
            xbmcgui.Dialog().ok(__language__(1201).encode( "utf-8", "ignore" ), __language__(1161).encode( "utf-8", "ignore" )) # Trakt Utilities, there are no tv shows in your watchlist
            return
        
        # display watchlist tv shows
        import windows
        ui = windows.TVShowsWindow("tvshows.xml", __settings__.getAddonInfo('path'), "Default")
        ui.initWindow(tvshows, 'watchlist')
        ui.doModal()
        del ui
    
    # list reccomended movies
    @staticmethod
    def recommendedMovies():

        movies = getRecommendedMovies()
        
        if movies == None: # movies = None => there was an error
            return # error already displayed in utilities.py
        
        if len(movies) == 0:
            xbmcgui.Dialog().ok(__language__(1201).encode( "utf-8", "ignore" ), __language__(1158).encode( "utf-8", "ignore" )) # Trakt Utilities, there are no movies recommended for you
            return
        
        # display recommended movies list
        import windows
        ui = windows.MoviesWindow("movies.xml", __settings__.getAddonInfo('path'), "Default")
        ui.initWindow(movies, 'recommended')
        ui.doModal()
        del ui
        
    # list reccomended tv shows
    @staticmethod
    def recommendedShows():

        tvshows = getRecommendedTVShowsFromTrakt()
        
        if tvshows == None: # tvshows = None => there was an error
            return # error already displayed in utilities.py
        
        if len(tvshows) == 0:
            xbmcgui.Dialog().ok(__language__(1201).encode( "utf-8", "ignore" ), __language__(1159).encode( "utf-8", "ignore" )) # Trakt Utilities, there are no tv shows recommended for you
            return
        
        for tvshow in tvshows:
            tvshow['watchlist'] = tvshow['in_watchlist']
            
        # display recommended tv shows
        import windows
        ui = windows.TVShowsWindow("tvshows.xml", __settings__.getAddonInfo('path'), "Default")
        ui.initWindow(tvshows, 'recommended')
        ui.doModal()
        del ui
    
    @staticmethod
    def trendingMovies():
    
        movies = getTrendingMovies()
        
        if movies == None: # movies = None => there was an error
            return # error already displayed in utilities.py
        
        if len(movies) == 0:
            xbmcgui.Dialog().ok("Trakt Utilities", "there are no trending movies")
            return
        
        # display trending movie list
        import windows
        ui = windows.MoviesWindow("movies.xml", __settings__.getAddonInfo('path'), "Default")
        ui.initWindow(movies, 'trending')
        ui.doModal()
        del ui

    @staticmethod
    def trendingShows():

        tvshows = getTrendingTVShowsFromTrakt()
        watchlist = traktShowListByTvdbID(getWatchlistTVShowsFromTrakt())
        
        if tvshows == None: # tvshows = None => there was an error
            return # error already displayed in utilities.py
        
        if len(tvshows) == 0:
            xbmcgui.Dialog().ok("Trakt Utilities", "there are no trending tv shows")
            return
        
        for tvshow in tvshows:
            if tvshow['imdb_id'] in watchlist:
                tvshow['watchlist'] = True
            else:
                tvshow['watchlist'] = False
        
        # display trending tv shows
        import windows
        ui = windows.TVShowsWindow("tvshows.xml", __settings__.getAddonInfo('path'), "Default")
        ui.initWindow(tvshows, 'trending')
        ui.doModal()
        del ui