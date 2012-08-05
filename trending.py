# -*- coding: utf-8 -*-
#

import xbmcaddon
import xbmcgui

try:
    import simplejson as json
except ImportError:
    import json

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

__author__ = "Ralph-Gordon Paul, Adrian Cowan"
__credits__ = ["Ralph-Gordon Paul", "Adrian Cowan", "Justin Nemeth",  "Sean Rudford"]
__license__ = "GPL"
__maintainer__ = "Ralph-Gordon Paul"
__email__ = "ralph-gordon.paul@uni-duesseldorf.de"
__status__ = "Production"

# read settings
__settings__ = xbmcaddon.Addon("script.traktutilities")
__language__ = __settings__.getLocalizedString

apikey = '0a698a20b222d0b8637298f6920bf03a'
username = __settings__.getSetting("username")
pwd = sha.new(__settings__.getSetting("password")).hexdigest()
debug = __settings__.getSetting("debug")
https = __settings__.getSetting('https')

if (https == 'true'):
    conn = httplib.HTTPSConnection('api.trakt.tv')
else:
    conn = httplib.HTTPConnection('api.trakt.tv')

headers = {"Content-type": "application/x-www-form-urlencoded", "Accept": "text/plain"}


def showTrendingMovies():

    movies = getTrendingMoviesFromTrakt()
    watchlist = traktMovieListByImdbID(getWatchlistMoviesFromTrakt())

    if movies == None:  # movies = None => there was an error
        return  # error already displayed in utilities.py

    if len(movies) == 0:
        xbmcgui.Dialog().ok("Trakt Utilities", "there are no trending movies")
        return

    for movie in movies:
        if movie['imdb_id'] in watchlist:
            movie['watchlist'] = True
        else:
            movie['watchlist'] = False

    # display trending movie list
    import windows
    ui = windows.MoviesWindow("movies.xml", __settings__.getAddonInfo('path'), "Default")
    ui.initWindow(movies, 'trending')
    ui.doModal()
    del ui


def showTrendingTVShows():

    tvshows = getTrendingTVShowsFromTrakt()
    watchlist = traktShowListByTvdbID(getWatchlistTVShowsFromTrakt())

    if tvshows == None:  # tvshows = None => there was an error
        return  # error already displayed in utilities.py

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
