# -*- coding: utf-8 -*-
# 

import xbmc,xbmcaddon
import * from utilities.py
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
        
        #receive latest according to trakt
        traktData = _copyTrakt()
        #get latest xbmc
        xbmcData = _copyXbmc()
        #threeway compare, xbmc-old(local)-trakt
        xbmcChanges, traktChanges, cacheChanges = _threeWayCompare(xbmcData, traktData)
        
        #perform local (ie to xbmc) changes
        _updateXbmc(xbmcChanges)
        #perform cache changes
        _updateCache(cacheChanges)
        #log remote (ie to trakt) changes into queue and send to trakt
        _updateTrakt(traktChanges)
        #update next sync times
        
        
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
    def _copyTrakt():
        traktData = {}
        
        movies = []
        traktMovies = getMoviesFromTrakt(daemon=True)
        watchlistMovies = traktMovieListByImdbID(getWatchlistMoviesFromTrakt())
        for movie in traktMovies:
            local = Movie.fromTrakt(movie)
            if local is None:
                continue
            if 'imdb_id' in movie:
                local._watchlistStatus = moviemovie['imdb_id'] in watchlistMovies
            movies[local._remoteId] = local
            
        
        shows = []
        #traktShows = getShowsFromTrakt(daemon=True)
        #for show in traktShows:
        #    shows.append(Show.fromTrakt(show))
            
        episodes = []
        #traktEpisodes = getEpisodesFromTrakt(daemon=True)
        #for episode in traktEpisodes:
        #    episodes.append(Episode.fromTrakt(episode))
            
        traktData['movies'] = movies
        traktData['shows'] = shows
        traktData['episodes'] = episodes
        return traktData
    
    @staticmethod
    def _copyXbmc():
        xbmcData = {}
        
        movies = []
        xbmcMovies = getMoviesFromXBMC()
        for movie in xbmcMovies:
            local = Movie.fromXbmc(movie)
            if local is None:
                continue
            movies[local._remoteId] = local
        
        shows = []
        #traktShows = getShowsFromTrakt(daemon=True)
        #for show in traktShows:
        #    shows.append(Show.fromTrakt(show))
            
        episodes = []
        #traktEpisodes = getEpisodesFromTrakt(daemon=True)
        #for episode in traktEpisodes:
        #    episodes.append(Episode.fromTrakt(episode))
            
        xbmcData['movies'] = movies
        xbmcData['shows'] = shows
        xbmcData['episodes'] = episodes
        return xbmcData
    
    @staticmethod
    def _threeWayCompare(xbmcData, traktData):
        for movie in _movies:
            if '_remoteId' not in movie:
                continue
            remoteId = movie['_remoteId']
            if remoteId not in traktData['movies']:
            if remoteId not in traktData['movies']:
            
        
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