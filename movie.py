# -*- coding: utf-8 -*-
# 

import xbmc,xbmcaddon
from utilities import *
import trakt_cache

__author__ = "Ralph-Gordon Paul, Adrian Cowan"
__credits__ = ["Ralph-Gordon Paul", "Adrian Cowan", "Justin Nemeth",  "Sean Rudford"]
__license__ = "GPL"
__maintainer__ = "Ralph-Gordon Paul"
__email__ = "ralph-gordon.paul@uni-duesseldorf.de"
__status__ = "Production"

__settings__ = xbmcaddon.Addon( "script.TraktUtilities" )
__language__ = __settings__.getLocalizedString

# Caches all information between the add-on and the web based trakt api
class Movie():
    _remoteId = None
    _title = None
    _year = None
    _playcount = 0
    _rating = None
    _watchlistStatus = False
    _recommendedStatus = False
    _libraryStatus = False
    
    def __init__(self, remoteId):
        if remoteId is None:
            raise ValueError("Must provide the id for the movie")
        self._remoteId = str(remoteId)
        
    def __repr__(self):
        return "<"+self._title+" ("+str(self._year)+") - "+self._remoteId+">"
        
    def __str__(self):
        return self._title+" ("+str(self._year)+")"
    
    def __getitem__(self, index):
        if index is "_remoteId": return self._remoteId
        if index is "_title": return self._title
        if index is "_year": return self._year
        if index is "_playcount": return self._playcount
        if index is "_rating": return self._rating
        if index is "_watchlistStatus": return self._watchlistStatus
        if index is "_recommendedStatus": return self._recommendedStatus
        if index is "_libraryStatus": return self._libraryStatus
    
    def __setitem__(self, index, value):
        if index is "_remoteId": self._remoteId = value
        if index is "_title": self._title = value
        if index is "_year": self._year = value
        if index is "_playcount": self._playcount = value
        if index is "_rating": self._rating = value
        if index is "_watchlistStatus": self._watchlistStatus = value
        if index is "_recommendedStatus": self._recommendedStatus = value
        if index is "_libraryStatus": self._libraryStatus = value
    
    def save(self):
        trakt_cache.saveMovie(self)
        
    def scrobble(self):
        raise NotImplementedError("This function has not been written")
    def rate(self, rating):
        raise NotImplementedError("This function has not been written")
    def shout(self, text):
        raise NotImplementedError("This function has not been written")
        
    def setRating(self, value):
        raise NotImplementedError("This function has not been written")
    def getRating(self):
        self._expireCheck()
        return _rating
        
    def setPlaycount(self, value):
        raise NotImplementedError("This function has not been written")
    def getPlaycount(self):
        self._expireCheck()
        return _playcount
        
    def setLibraryStatus(self, value):
        raise NotImplementedError("This function has not been written")
    def getLibraryStatus(self):
        self._expireCheck('movielibrary')
        return _libraryStatus
        
    def setWatchingStatus(self, value):
        raise NotImplementedError("This function has not been written")
    def getWatchingStatus(self):
        raise NotImplementedError("This function has not been written")
        
    def setWatchlistStatus(self, value):
        raise NotImplementedError("This function has not been written")
    def getWatchlistStatus(self):
        self._expireCheck('moviewatchlist')
        return _watchlistStatus
        
    def getRecommendedStatus(self):
        self._expireCheck('movierecommended')
        return _recommendedStatus
    
    def _expireCheck(self, state=None):
        if state is not None:
            if state in _expire and _expire[state] >= time.time():
                return
        if self._remoteId not in _expire or _expire[_remoteId] < time.time():
            refreshMovie(_remoteId)
    
    @staticmethod
    def download(remoteId):
        Debug("[Movie] Downloading info for "+str(Movie.devolveId(remoteId)))
        local = getMovieFromTrakt(Movie.devolveId(remoteId))
        if local is None:
            return None
        return Movie.fromTrakt(local)
    
    def traktise(self):
        movie = {}
        movie['title'] = _title
        movie['year'] = _year
        movie['plays'] = _playcount
        movie['in_watchlist'] = _watchlistStatus
        movie['in_collection'] = _libraryStatus
        if str(_remoteId).find('imbd=') == 0:
            movie['imdb_id'] = _remoteId[5:]
        if str(_remoteId).find('tmbd=') == 0:
            movie['tmdb_id'] = _remoteId[5:]
        return movie
        
    @staticmethod
    def fromTrakt(movie):
        if 'imdb_id' in movie:
            local = Movie("imdb="+movie['imdb_id'])
        elif 'tmdb_id' in movie:
            local = Movie("tmdb="+movie['tmdb_id'])
        else:
            return None
        local._title = movie['title']
        local._year = movie['year']
        local._playcount = movie['plays']
        if 'in_watchlist' in movie:
            local._watchlistStatus = movie['in_watchlist']
        if 'in_collection' in movie:
            local._libraryStatus = movie['in_collection']
        return local
     
    @staticmethod
    def fromXbmc(movie):
        #Debug("[Movie] Creating from: "+str(movie))
        if 'imdbnumber' not in movie or movie['imdbnumber'].strip() == "":
            remoteId = trakt_cache.getMovieId(movie['movieid'])
            if remoteId is not None:
                local = Movie(remoteId)
            else:
                traktMovie = searchTraktForMovie(movie['title'], movie['year'])
                if traktMovie is None:
                    return None
                if 'imdb_id' in traktMovie:
                    local = Movie("imdb="+traktMovie['imdb_id'])
                elif 'tmdb_id' in traktMovie:
                    local = Movie("tmdb="+traktMovie['tmdb_id'])
                else:
                    return None
                # Related movieid to remoteId, now store the relationship
                trakt_cache.relateMovieId(movie['movieid'], local['_remoteId'])
        else:
            local = Movie(Movie.evolveId(movie['imdbnumber']))
        local._title = movie['title']
        local._year = movie['year']
        local._playcount = movie['playcount']
        return local
    
    @staticmethod
    def evolveId(idString):
        if idString.find('tt') == 0:
            return str("imdb="+idString.strip())
        else:
            return str("tmdb="+idString.strip())
    
    @staticmethod
    def devolveId(idString):
        #Debug("[Movie] Devolving id: "+str(idString))
        if idString.find('imdb=tt') == 0:
            return idString[5:]
        elif idString.find('imdb=') == 0:
            return "tt"+idString[5:]
        elif idString.find('tmbd=') == 0:
            return idString[5:]
        