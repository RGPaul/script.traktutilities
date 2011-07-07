# -*- coding: utf-8 -*-
# 

import xbmc,xbmcaddon
import time
import shelve

__author__ = "Ralph-Gordon Paul, Adrian Cowan"
__credits__ = ["Ralph-Gordon Paul", "Adrian Cowan", "Justin Nemeth",  "Sean Rudford"]
__license__ = "GPL"
__maintainer__ = "Ralph-Gordon Paul"
__email__ = "ralph-gordon.paul@uni-duesseldorf.de"
__status__ = "Production"

__settings__ = xbmcaddon.Addon( "script.TraktUtilities" )
__language__ = __settings__.getLocalizedString

# Caches all information between the add-on and the web based trakt api
class TraktCache:
    _location = None
    _movies = None
    _shows = None
    _episodes = None
    
    @staticmethod
    def init(location=None):
        _location = location
        if _location is not None:
            TraktCache._fill()
        
    @staticmethod
    def _fill():
        _movies = shelve.open(_location+".movies")
        _shows = shelve.open(_location+".shows")
        _episodes = shelve.open(_location+".episodes")
        _expire = shelve.open(_location+".ttl")
        
    @staticmethod
    def getMovie(remoteId = None, localId = None):
        if remoteId is None and localId is None:
            raise ValueError("Must provide at least one form of id")
        if remoteId is None:
            if '_byLocalId' in _movies and localId in _movies['_byLocalId']:
                remoteId = _movies['_byLocalId'][localId]
        if remoteId is None or remoteId not in _movies:
            raise ValueError("Unknown movie")
        return _movies[remoteId]
        
    @staticmethod
    def getMovieWatchList():
        if 'moviewatchlist' not in _expire or _expire['moviewatchlist'] < time.gmtime():
            refreshMovieWatchlist()
        watchlist = []
        for movie in _movies:
            if 'watchlist' in movie and movie['watchlist'] == True:
                watchlist.append(movie)