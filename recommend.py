# -*- coding: utf-8 -*-
# 

import xbmc,xbmcaddon,xbmcgui
from utilities import *

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

# list reccomended movies
def showRecommendedMovies():

    movies = getRecommendedMoviesFromTrakt()
    watchlist = traktMovieListByImdbID(getWatchlistMoviesFromTrakt())
    
    if movies == None: # movies = None => there was an error
        return # error already displayed in utilities.py
    
    if len(movies) == 0:
        xbmcgui.Dialog().ok(__language__(1201).encode( "utf-8", "ignore" ), __language__(1158).encode( "utf-8", "ignore" )) # Trakt Utilities, there are no movies recommended for you
        return
    
    for movie in movies:
        if movie['imdb_id'] in watchlist:
            movie['watchlist'] = True
        else:
            movie['watchlist'] = False
    
    # display recommended movies list
    import windows
    ui = windows.MoviesWindow("movies.xml", __settings__.getAddonInfo('path'), "Default")
    ui.initWindow(movies, 'recommended')
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
    
    for tvshow in tvshows:
        tvshow['watchlist'] = tvshow['in_watchlist']
        
    # display recommended tv shows
    import windows
    ui = windows.TVShowsWindow("tvshows.xml", __settings__.getAddonInfo('path'), "Default")
    ui.initWindow(tvshows, 'recommended')
    ui.doModal()
    del ui
    
