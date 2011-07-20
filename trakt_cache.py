# -*- coding: utf-8 -*-
# 

import xbmc,xbmcaddon
from utilities import *
from movie import *
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

_location = None
_movies = None
_shows = None
_episodes = None
_expire = None


def init(location=None):
    trakt_cache._location = xbmc.translatePath(location)
    if trakt_cache._location is not None:
        trakt_cache._fill()
        #if 'all' not in trakt_cache._expire or trakt_cache._expire['all'] < time.time():
        trakt_cache._sync()
    

def _fill():
    trakt_cache._movies = shelve.open(trakt_cache._location+".movies")
    trakt_cache._shows = shelve.open(trakt_cache._location+".shows")
    trakt_cache._episodes = shelve.open(trakt_cache._location+".episodes")
    trakt_cache._expire = shelve.open(trakt_cache._location+".ttl")
    

def _sync():
    Debug("[TraktCache] Syncronising")
    # Send changes to trakt
    trakt_cache._updateTrakt()
    
    # Receive latest according to trakt
    traktData = trakt_cache._copyTrakt()
    # Get latest xbmc
    xbmcData = trakt_cache._copyXbmc()
    # Find and list all changes
    xbmcChanges = trakt_cache._syncCompare(traktData)
    traktChanges = trakt_cache._syncCompare(xbmcData, xbmc = True)
    
    # Find unanimous changes and direct them to the cache
    cacheChanges = {}
    cacheChanges['movies'] = []
    cacheChanges['shows'] = []
    cacheChanges['episodes'] = []
    
    for type in ['movies', 'shows', 'episodes']:
        for change in xbmcChanges[type]:
            if change in traktChanges[type]: # I think this works, but my concern is that it wont compare the values
                traktChanges[type].remove(change)
                xbmcChanges[type].remove(change)
                cacheChanges[type].append(change)
    
    # Perform cache only changes
    Debug("[TraktCache] Updating cache")
    trakt_cache._updateCache(cacheChanges, traktData)
    # Perform local (ie to xbmc) changes
    Debug("[TraktCache] Updating xbmc")
    trakt_cache._updateXbmc(xbmcChanges)
    # Log remote (ie to trakt) changes into queue and send to trakt
    Debug("[TraktCache] Updateing trakt")
    trakt_cache._updateTrakt(traktChanges)
    # Update next sync times
    trakt_cache.updateAllSyncTimes()


def _updateCache(changes, traktData = {}):
    if 'movies' in changes:
        for change in changes['movies']:
            Debug("[TraktCache] Cache update: "+repr(change))
            if 'remoteId' in change and 'subject' in change and 'value' in change:
                if change['subject'] in ('playcount', 'rating', 'watchlistStatus', 'recommendedStatus', 'libraryStatus'):
                    if change['remoteId'] in _movies:
                        movie = _movies[change['remoteId']]
                        Debug("[TraktCache] Updating "+str(movie)+", setting "+str(change['subject'])+" to "+str(change['value']))
                        movie['_'+change['subject']] = change['value']
                        _movies[change['remoteId']] = movie
                    else:
                        if 'movies' in traktData and change['remoteId'] in traktData['movies']:
                            Debug("[TraktCache] Inserting into cache from local trakt data")
                            _movies[change['remoteId']] = traktData['movies'][change['remoteId']]
                        else:
                            Debug("[TraktCache] Inserting into cache from remote trakt data")
                            _movies[change['remoteId']] = Movie.download(change['remoteId'])


def _updateXbmc(changes):
    cacheChanges = {}
    
    if 'movies' in changes:
        cacheChanges['movies'] = []
        for change in changes['movies']:
            Debug("[TraktCache] XBMC update: "+repr(change))
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
                cacheChanges['movies'].append(change)
    _updateCache(cacheChanges)        

def _updateTrakt(newChanges = None):
    changeQueue = {}
    if '_queue' in trakt_cache._movies:
        changeQueue['movies'] = trakt_cache._movies['_queue']
    else:
        changeQueue['movies'] = []
        
    if '_queue' in trakt_cache._shows:
        changeQueue['shows'] = trakt_cache._shows['_queue']
    else:
        changeQueue['shows'] = []
        
    if '_queue' in trakt_cache._episodes:
        changeQueue['episodes'] = trakt_cache._episodes['_queue']
    else:
        changeQueue['episodes'] = []
    
    if newChanges is not None:
        if 'movies' in newChanges:
            # Add and new changes to the queue
            for change in newChanges['movies']:
                if change not in changeQueue['movies']: # Check that we arn't adding duplicates
                    changeQueue['movies'].append(change)
            
            trakt_cache._movies['_queue'] = changeQueue['movies']
    
    cacheChanges = {}
    
    if 'movies' in changeQueue:
        cacheChanges['movies'] = []
        for change in changeQueue['movies']:
            Debug("[TraktCache] trakt update: "+repr(change))
            if 'remoteId' in change and 'subject' in change and 'value' in change:
                if change['subject'] == 'watchlistStatus':
                    if change['remoteId'] in trakt_cache._movies and '_watchlistStatus' in trakt_cache._movies[change['remoteId']]:
                        movie = trakt_cache._movies[change['remoteId']]
                        if change['value'] == True:
                            if addMoviesToWatchlist([movie.traktise()]) is None:
                                continue # failed, leave in queue for next time
                        else:
                            if removeMoviesFromWatchlist([movie.traktise()]) is None:
                                continue # failed, leave in queue for next time
                elif change['subject'] == 'playcount':
                    if change['remoteId'] in trakt_cache._movies and '_playcount' in trakt_cache._movies[change['remoteId']]:
                        movie = trakt_cache._movies[change['remoteId']]
                        movie._playcount = change['value']
                        if setMoviesPlaycountOnTrakt([movie.traktise()]) is None:
                            continue # failed, leave in queue for next time
                elif change['subject'] == 'watchingStatus':
                    if change['remoteId'] in _movies and '_watchingStatus' in _movies[change['remoteId']]:
                        movie = trakt_cache._movies[change['remoteId']]
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
                    queue = trakt_cache._movies['_queue']
                    queue.remove(change)
                    trakt_cache._movies['_queue'] = queue
                    continue
                # succeeded
                cacheChanges['movies'].append(change)
            # either succeeded or invalid
            queue = trakt_cache._movies['_queue']
            queue.remove(change)
            trakt_cache._movies['_queue'] = queue
    trakt_cache._updateCache(cacheChanges)


def _copyTrakt():
    traktData = {}
    
    movies = {}
    traktMovies = getMoviesFromTrakt(daemon=True)
    watchlistMovies = traktMovieListByImdbID(getWatchlistMoviesFromTrakt())
    for movie in traktMovies:
        local = Movie.fromTrakt(movie)
        if local is None:
            continue
        if 'imdb_id' in movie:
            local._watchlistStatus = movie['imdb_id'] in watchlistMovies
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

def _copyXbmc():
    xbmcData = {}
    
    movies = {}
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


def _listChanges(newer, older, attributes, xbmc = False):
    changes = []
    # Find new items
    for remoteId in newer:
        if remoteId[0] == '_': continue
        newItem = newer[remoteId]
        if newItem['_remoteId'] not in older:
            for attribute in attributes:
                changes.append({'remoteId': remoteId, 'subject': attribute, 'value':newItem['_'+attribute]})
    
    for remoteId in older:
        if remoteId[0] == '_': continue
        oldItem = older[remoteId]
        if oldItem is None:
            del older[remoteId]
            continue
        if remoteId not in newer: #If item removed from library
            changes.append({'remoteId': remoteId, 'subject': 'libraryStatus', 'value':False})
        else:
            newItem = newer[remoteId]
            if newItem is None:
                del newer[remoteId]
                continue
            for attribute in attributes:
                if newItem['_'+attribute] <> oldItem['_'+attribute]: # If the non cached data is different from the old data cached locally
                    changes.append({'remoteId': remoteId, 'subject': attribute, 'value':newItem['_'+attribute]})
    return changes


def relateMovieId(localId, remoteId):
    if '_byLocalId' in trakt_cache._movies:
        index = trakt_cache._movies['_byLocalId']
    else:
        index = {}
    index[localId] = remoteId
    trakt_cache._movies['_byLocalId'] = index
    

def getMovieId(localId):
    if '_byLocalId' in trakt_cache._movies and localId in trakt_cache._movies['_byLocalId']:
        return trakt_cache._movies['_byLocalId'][localId]
    return None


def updateAllSyncTimes():
    trakt_cache._expire['moviewatchlist'] = time.time() + 10*60 # +10mins
    trakt_cache._expire['movierecommended'] = time.time() + 30*60 # +30mins
    trakt_cache._expire['movielibrary'] = time.time() + 6*60*60 # +6hours
    trakt_cache._expire['movieall'] = time.time() + 6*60*60 # +6hours
    trakt_cache._expire['all'] = time.time() + 6*60*60 # +6hours
    for remoteId in _movies:
        trakt_cache._expire[remoteId] = time.time() + 10*60 # +10mins


def getMovie(remoteId = None, localId = None):
    if remoteId is None and localId is None:
        raise ValueError("Must provide at least one form of id")
    if remoteId is None:
        remoteId = trakt_cache.getMovieId(localId)
    if remoteId is None:
        raise ValueError("Unknown movie")
    if remoteId not in trakt_cache._expire or trakt_cache._expire[remoteId] < time.time():
        refreshMovie(remoteId)
    if remoteId not in trakt_cache._movies:
        raise "Bad, logic bomb"
    return trakt_cache._movies[remoteId]


def refreshMovie(remoteId):
    if remoteId in _movies:
        changes = _listChanges([Movie.download(remoteId)],[_movies[remoteId]], ['playcount', 'rating', 'watchlistStatus', 'libraryStatus'])
        _updateCache(changes)
    else:
        _movies[remoteId] = Movie.download(remoteId)
    trakt_cache._expire[remoteId] = time.time() + 10*60 # +10mins


def saveMovie(movie):
    if remoteId not in movie:
        raise ValueError("Invalid movie")
    _shows[movie.remoteId] = movie


def getMovieWatchList():
    if 'moviewatchlist' not in trakt_cache._expire or trakt_cache._expire['moviewatchlist'] < time.time():
        trakt_cache.refreshMovieWatchlist()
    watchlist = []
    for remoteId in trakt_cache._movies:
        if remoteId[0] == '_': continue
        movie = trakt_cache._movies[remoteId]
        if movie is None:
            del trakt_cache._movies[remoteId]
            continue
        if movie['_watchlistStatus']:
            watchlist.append(movie)
    return watchlist


def refreshMovieWatchlist():
    Debug("[Cache] Refreshing watchlist")
    traktWatchlist = getWatchlistMoviesFromTrakt()
    watchlist = {}
    for movie in traktWatchlist:
        remoteId = Movie.evolveId(movie['imdb_id'])
        watchlist[remoteId] = None
        if remoteId not in trakt_cache._movies:
            trakt_cache._movies[remoteId] = Movie.fromTrakt(movie)
    for remoteId in trakt_cache._movies:
        if remoteId[0] == '_': continue
        movie = trakt_cache._movies[remoteId]
        if movie is None:
            del trakt_cache._movies[remoteId]
            continue
        if movie['_watchlistStatus'] <> (remoteId in watchlist):
            movie['_watchlistStatus'] = not movie['_watchlistStatus']
            trakt_cache._movies[movie['_remoteId']] = movie
    trakt_cache._expire['moviewatchlist'] = time.time() + 10*60 # +10mins
    
    
