# -*- coding: utf-8 -*-
# 

import xbmc,xbmcaddon
from trakt_cache import TraktCache

__author__ = "Ralph-Gordon Paul, Adrian Cowan"
__credits__ = ["Ralph-Gordon Paul", "Adrian Cowan", "Justin Nemeth",  "Sean Rudford"]
__license__ = "GPL"
__maintainer__ = "Ralph-Gordon Paul"
__email__ = "ralph-gordon.paul@uni-duesseldorf.de"
__status__ = "Production"

__settings__ = xbmcaddon.Addon( "script.TraktUtilities" )
__language__ = __settings__.getLocalizedString

# Caches all information between the add-on and the web based trakt api
class Show:
    _remoteId
    _title
    _year
    _playcount
    _watchlistStatus
    _recommendedStatus
    _libraryStatus
    
    def __init__(self, remoteId):
        if remoteId is None:
            raise ValueError("Must provide the id for the movie")
        self._remoteId = remoteId
        
    def save(self):
        TraktCache.saveMovie(self)
        
    def scrobble(self):
        raise NotImplementedError("This function has not been written")
    def rate(self, rating):
        raise NotImplementedError("This function has not been written")
    def shout(self, text):
        raise NotImplementedError("This function has not been written")
        
    def setSeenStatus(self, value):
        raise NotImplementedError("This function has not been written")
    def getSeenStatus(self):
        raise NotImplementedError("This function has not been written")
        
    def setLibraryStatus(self, value):
        raise NotImplementedError("This function has not been written")
    def getLibraryStatus(self):
        raise NotImplementedError("This function has not been written")
        
    def setWatchingStatus(self, value):
        raise NotImplementedError("This function has not been written")
    def getWatchingStatus(self):
        raise NotImplementedError("This function has not been written")
        
    def setWatchlistStatus(self, value):
        raise NotImplementedError("This function has not been written")
    def getWatchlistStatus(self):
        raise NotImplementedError("This function has not been written")
        
    def traktise(self):
        show = {}
        show['title'] = _title
        show['year'] = _year
        show['plays'] = _playcount
        show['in_watchlist'] = _watchlistStatus
        show['in_collection'] = _libraryStatus
        if str(_remoteId).find('tvbd=') == 0:
            show['tvdb_id'] = _remoteId[5:]
        if str(_remoteId).find('imbd=') == 0:
            show['imdb_id'] = _remoteId[5:]
        return show
        
    @staticmethod
    def fromTrakt(show):
        if 'tvdb_id' in show:
            local = Show("tvdb="+show['tvdb_id'])
        else if 'imdb_id' in movie:
            local = Show("imdb="+show['imdb_id'])
        else
            return None
        local._title = show['title']
        local._year = show['year']
        local._playcount = show['plays']
        local._watchlistStatus = show['in_watchlist']
        local._libraryStatus = show['in_collection']
        return local