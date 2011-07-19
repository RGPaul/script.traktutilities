# -*- coding: utf-8 -*-
# 

import xbmc,xbmcaddon
from utilities import *
from movie import Movie
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
    _expire = None
    
    @staticmethod
    def init(location=None):
        TraktCache._location = xbmc.translatePath(location)
        if TraktCache._location is not None:
            TraktCache._fill()
        
    @staticmethod
    def _fill():
        TraktCache._movies = shelve.open(TraktCache._location+".movies")
        TraktCache._shows = shelve.open(TraktCache._location+".shows")
        TraktCache._episodes = shelve.open(TraktCache._location+".episodes")
        TraktCache._expire = shelve.open(TraktCache._location+".ttl")
        
    @staticmethod
    def _sync():
        # Send changes to trakt
        _updateTrakt()
        
        # Receive latest according to trakt
        traktData = _copyTrakt()
        # Get latest xbmc
        xbmcData = _copyXbmc()
        # Find and list all changes
        xbmcChanges = _syncCompare(traktData)
        traktChanges = _syncCompare(xbmcData, xbmc = True)
        
        # Find unanimous changes and direct them to the cache
        cacheChanges = []
        for change in xbmcChanges:
            if change in traktChanges: # I think this works, but my concern is that it wont compare the values
                traktChanges.remove(change)
                xbmcChanges.remove(change)
                cacheChanges.append(change)
        
        # Perform cache only changes
        _updateCache(cacheChanges, traktData)
        # Perform local (ie to xbmc) changes
        _updateXbmc(xbmcChanges)
        # Log remote (ie to trakt) changes into queue and send to trakt
        _updateTrakt(traktChanges)
        # Update next sync times
        updateAllSyncTimes()
    
    @staticmethod
    def _updateCache(changes, traktData = []):
        for change in changes:
            if 'remoteId' in change and 'subject' in change and 'value' in change:
                if change['subject'] in ('playcount', 'rating', 'watchlistStatus', 'recommendedStatus', 'libraryStatus'):
                    if change['remoteId'] in _movies:
                        if '_'+change['subject'] in _movies[change['remoteId']]:
                            movie = _movies[change['remoteId']]
                            movie['_'+change['subject']] = change['value']
                            _movies[change['remoteId']] = movie
                        else:
                            if change['remoteId'] in traktData:
                                _movies[change['remoteId']] = traktData[change['remoteId']]
                            else:
                                _movies[change['remoteId']] = Movie.download(change['remoteId'])
    
    @staticmethod
    def _updateXbmc(changes):
        cacheChanges = []
        
        for change in changes:
            if 'remoteId' in change and 'subject' in change and 'value' in change:
                if change['subject'] == 'playcount':
                    if change['remoteId'] in _movies and '_playcount' in _movies[change['remoteId']]:
                        if setXBMCMoviePlaycount(Movie.devolveId(change['remoteId']), change['value']) is None:
                            continue # failed, skip
                elif change['subject'] in ('watchlistStatus', 'watchingStatus', 'libraryStatus', 'rating'):
                    # ignore, irrelevant (suppost to be impossible to get here)
                    continue
                else:
                    # invalid
                    continue
                # succeeded
                cacheChanges.append(change)
        _updateCache(cacheChanges)        
    @staticmethod
    def _updateTrakt(newChanges):
        changeQueue = _movies['_queue']
        cacheChanges = []
        
        # Add and new changes to the queue
        for change in newChanges:
            if change not in changeQueue: # Check that we arn't adding duplicates
                changeQueue.append(change)
        
        _movies['_queue'] = changeQueue
        
        for change in changeQueue:
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
                elif change['subject'] == 'playcount':
                    if change['remoteId'] in _movies and '_playcount' in _movies[change['remoteId']]:
                        movie = _movies[change['remoteId']]
                        movie._playcount = change['value']
                        if setMoviesPlaycountOnTrakt([movie.traktise()]) is None:
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
                else:
                    # invalid
                    _movies['_queue'].remove(change)
                    continue
                # succeeded
                cacheChanges.append(change)
            # either succeeded or invalid
            _movies['_queue'].remove(change)
        _updateCache(cacheChanges)
    
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
    def _syncCompare(data, xbmc = False):
        if xbmc:
            movieAttributes = ['playcount']
            showAttributes = []
            episodeAttributes = ['playcount']
        else:
            movieAttributes = ['playcount', 'rating', 'watchlistStatus', 'recommendedStatus', 'libraryStatus']
            showAttributes = ['rating', 'watchlistStatus', 'recommendedStatus']
            episodeAttributes = ['playcount', 'rating', 'watchlistStatus', 'libraryStatus']
        
        changes = {}
        # Compare movies
        changes['movies'] = _listChanges(data['movies'], _movies, movieAttributes, xbmc)
        # Compare TV shows
        changes['shows'] = _listChanges(data['shows'], _shows, showAttributes, xbmc)
        # Compare TV episodes
        changes['episodes'] = _listChanges(data['episodes'], _episodes, episodeAttributes, xbmc)
        
        return changes
    
    @staticmethod
    def _listChanges(newer, older, attributes, xbmc = False):
        # Find new items
        for newItem in newer:
            if newItem['_remoteId'] not in older:
                for attribute in attributes:
                    changes.append({'remoteId': remoteId, 'subject': attribute, 'value':newItem['_'+attribute]})
        
        for oldItem in older:
            remoteId = oldItem['_remoteId']
            if remoteId not in newer: #If item removed from library
                changes.append({'remoteId': remoteId, 'subject': 'libraryStatus', 'value':False})
            else:
                newItem = newer[remoteId]
                for attribute in attributes:
                    if newItem['_'+attribute] <> oldItem['_'+attribute]: # If the non cached data is different from the old data cached locally
                        changes.append({'remoteId': remoteId, 'subject': attribute, 'value':newItem['_'+attribute]})
    
    @staticmethod
    def updateAllSyncTimes():
        TraktCache._expire['moviewatchlist'] = time.time() + 10*60 # +10mins
        TraktCache._expire['movierecommended'] = time.time() + 30*60 # +30mins
        TraktCache._expire['movielibrary'] = time.time() + 6*60*60 # +6hours
        TraktCache._expire['movieall'] = time.time() + 6*60*60 # +6hours
        for remoteId in _movies:
            TraktCache._expire[remoteId] = time.time() + 10*60 # +10mins
    
    @staticmethod
    def getMovie(remoteId = None, localId = None):
        if remoteId is None and localId is None:
            raise ValueError("Must provide at least one form of id")
        if remoteId is None:
            if '_byLocalId' in _movies and localId in _movies['_byLocalId']:
                remoteId = _movies['_byLocalId'][localId]
        if remoteId is None:
            raise ValueError("Unknown movie")
        if remoteId not in TraktCache._expire or TraktCache._expire[remoteId] < time.time():
            refreshMovie(remoteId)
        if remoteId not in _movies:
            raise "Bad, logic bomb"
        return _movies[remoteId]
    
    @staticmethod
    def refreshMovie(remoteId):
        if remoteId in _movies:
            changes = _listChanges([Movie.download(remoteId)],[_movies[remoteId]], ['playcount', 'rating', 'watchlistStatus', 'libraryStatus'])
            _updateCache(changes)
        else:
            _movies[remoteId] = Movie.download(remoteId)
        TraktCache._expire[remoteId] = time.time() + 10*60 # +10mins
    
    @staticmethod
    def saveMovie(movie):
        if remoteId not in movie:
            raise ValueError("Invalid movie")
        _shows[movie.remoteId] = movie
    
    @staticmethod
    def getMovieWatchList():
        #if 'moviewatchlist' not in TraktCache._expire or TraktCache._expire['moviewatchlist'] < time.time():
        TraktCache.refreshMovieWatchlist()
        watchlist = []
        for remoteId in TraktCache._movies:
            movie = TraktCache._movies[remoteId]
            if movie['_watchlistStatus']:
                watchlist.append(movie)
        return watchlist
    
    @staticmethod
    def refreshMovieWatchlist():
        Debug("[Cache] Refreshing watchlist")
        traktWatchlist = getWatchlistMoviesFromTrakt()
        watchlist = {}
        for movie in traktWatchlist:
            remoteId = Movie.evolveId(movie['imdb_id'])
            watchlist[remoteId] = None
            if remoteId not in TraktCache._movies:
                TraktCache._movies[remoteId] = Movie.fromTrakt(movie)
        for remoteId in TraktCache._movies:
            if remoteId == '_queue': continue
            movie = TraktCache._movies[remoteId]
            
            if movie['_watchlistStatus'] <> (remoteId in watchlist):
                movie['_watchlistStatus'] = not movie['_watchlistStatus']
                TraktCache._movies[movie['_remoteId']] = movie
        TraktCache._expire['moviewatchlist'] = time.time() + 10*60 # +10mins
    
    
