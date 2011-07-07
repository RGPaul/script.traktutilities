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
    def _sync():
        #send changes to trakt
        _attemptResend()
        #receive latest accordign to trakt
        
        #check for diff between local(trakt) and xbmc
        
        #log changes into queue and send to trakt
        
    @staticmethod
    def _attemptResend():
        for change in _movies['_queue']:
            if 'remoteId' in change and 'subject' in change and 'value' in change:
                if change['subject'] == 'watchlistStatus':
                    if change['remoteId'] in _movies and '_watchlistStatus' in _movies[change['remoteId']]:
                        movie = _movies[change['remoteId']]
                        if change['value'] == True:
                            if addMoviesToWatchlist([movie.traktise()]) is None:
                                continue # failed, leave in queue for next time
                        else:
                            if removeMoviesFromWatchlist([movie.traktise()]) is None:
                                continue # failed, leave in queue for next time
                elif change['subject'] == 'seenStatus':
                    if change['remoteId'] in _movies and '_playcount' in _movies[change['remoteId']]:
                        movie = _movies[change['remoteId']]
                        if change['value'] >= 1:
                            if setMoviesSeenOnTrakt([movie.traktise()]) is None:
                                continue # failed, leave in queue for next time
                        else:
                            if setMoviesUnseenOnTrakt([movie.traktise()]) is None:
                                continue # failed, leave in queue for next time
                elif change['subject'] == 'watchingStatus':
                    if change['remoteId'] in _movies and '_watchingStatus' in _movies[change['remoteId']]:
                        movie = _movies[change['remoteId']]
                        if change['value'] == True:
                            if watchingMovieOnTrakt() is None:
                                continue # failed, leave in queue for next time
                        else:
                            if cancelWatchingMovieOnTrakt([movie.traktise()]) is None:
                                continue # failed, leave in queue for next time
                elif change['subject'] == 'libraryStatus':
                    continue
                elif change['subject'] == 'rating':
                    continue
                elif change['subject'] == 'scrobble':
                    continue
            # either succeeded or invalid
            _movies['_queue'].remove(change)
        
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
    def saveMovie(movie):
        if remoteId not in movie:
            raise ValueError("Invalid movie")
        _shows[movie.remoteId] = movie
    
    @staticmethod
    def getMovieWatchList():
        if 'moviewatchlist' not in _expire or _expire['moviewatchlist'] < time.gmtime():
            refreshMovieWatchlist()
        watchlist = []
        for movie in _movies:
            if 'watchlist' in movie and movie['watchlist'] == True:
                watchlist.append(movie)