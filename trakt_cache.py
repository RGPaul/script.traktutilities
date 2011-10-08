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
        needSyncAtLeast(['library'],force=True)
    

def _fill():
    trakt_cache._movies = shelve.open(trakt_cache._location+".movies")
    trakt_cache._shows = shelve.open(trakt_cache._location+".shows")
    trakt_cache._episodes = shelve.open(trakt_cache._location+".episodes")
    trakt_cache._expire = shelve.open(trakt_cache._location+".ttl")
    

def _sync(xbmcData = None, traktData = None):
    Debug("[TraktCache] Syncronising")
    
    if xbmcData is not None and 'movies' not in xbmcData: xbmcData['movies'] = []
    if traktData is not None and 'movies' not in traktData: traktData['movies'] = []
    if xbmcData is not None and 'shows' not in xbmcData: xbmcData['shows'] = []
    if traktData is not None and 'shows' not in traktData: traktData['shows'] = []
    if xbmcData is not None and 'episodes' not in xbmcData: xbmcData['episodes'] = []
    if traktData is not None and 'episodes' not in traktData: traktData['episodes'] = []
    
    # Find and list all changes
    if traktData is not None:
        xbmcChanges = trakt_cache._syncCompare(traktData)
        Debug("[~] X"+repr(xbmcChanges))
    #Debug("[~] xD"+repr(xbmcData))
    #Debug("[~] cD"+str(_movies))
    if xbmcData is not None:
        traktChanges = trakt_cache._syncCompare(xbmcData, xbmc = True)
        Debug("[~] T"+repr(traktChanges))
        
    # Find unanimous changes and direct them to the cache
    cacheChanges = {}
    cacheChanges['movies'] = []
    cacheChanges['shows'] = []
    cacheChanges['episodes'] = []
    
    if traktData is not None and xbmcData is not None:
        for type in ['movies', 'shows', 'episodes']:
            for xbmcChange in xbmcChanges[type]:
                for traktChange in traktChanges[type]: # I think this works, but my concern is that it wont compare the values
                    if (xbmcChange['remoteId'] == traktChange['remoteId'] and xbmcChange['subject'] == traktChange['subject']):
                        traktChanges[type].remove(traktChange)
                        xbmcChanges[type].remove(xbmcChange)
                        cacheChanges[type].append(traktChange)
                        
    # Perform cache only changes
    Debug("[TraktCache] Updating cache")
    trakt_cache._updateCache(cacheChanges, traktData)
    if traktData is not None:
        # Perform local (ie to xbmc) changes
        Debug("[TraktCache] Updating xbmc")
        trakt_cache._updateXbmc(xbmcChanges, traktData)
    if xbmcData is not None:
        # Log remote (ie to trakt) changes into queue and send to trakt
        Debug("[TraktCache] Updateing trakt")
        trakt_cache._updateTrakt(traktChanges, traktData)
    # Update next sync times
    trakt_cache.updateSyncTimes(['library'], _movies.keys())

def refreshLibrary():
    # Send changes to trakt
    trakt_cache._updateTrakt()
    
    # Receive latest according to trakt
    traktData = trakt_cache._copyTrakt()
    # Get latest xbmc
    xbmcData = trakt_cache._copyXbmc()
    
    _sync(xbmcData, traktData)

def _updateCache(changes, traktData = {}):
    if 'movies' in changes:
        for change in changes['movies']:
            Debug("[TraktCache] Cache update: "+repr(change))
            if 'remoteId' in change and 'subject' in change and 'value' in change:
                if change['subject'] in ('playcount', 'rating', 'watchlistStatus', 'recommendedStatus', 'libraryStatus'):
                    if change['remoteId'] in _movies:
                        movie = _movies[change['remoteId']]
                        Debug("[TraktCache] Updating "+unicode(movie)+", setting "+str(change['subject'])+" to "+str(change['value']))
                        movie['_'+change['subject']] = change['value']
                        _movies[change['remoteId']] = movie
                    else:
                        if 'movies' in traktData and change['remoteId'] in traktData['movies']:
                            Debug("[TraktCache] Inserting into cache from local trakt data: "+repr(traktData['movies'][change['remoteId']]))
                            _movies[change['remoteId']] = traktData['movies'][change['remoteId']]
                        else:
                            Debug("[TraktCache] Inserting into cache from remote trakt data")
                            _movies[change['remoteId']] = Movie.download(change['remoteId'])

def _updateXbmc(changes, traktData = {}):
    cacheChanges = {}
    
    if 'movies' in changes:
        cacheChanges['movies'] = []
        for change in changes['movies']:
            Debug("[TraktCache] XBMC update: "+repr(change))
            if 'remoteId' in change and 'subject' in change and 'value' in change:
                if change['subject'] == 'playcount':
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
    _updateCache(cacheChanges, traktData)        

def _updateTrakt(newChanges = None, traktData = {}):
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
                    movie = Movie(change['remoteId'])
                    movie._playcount = change['value']
                    if (movie._playcount >= 0):
                        if (movie._playcount == 0):
                            if setMoviesUnseenOnTrakt([movie.traktise()]) is None:
                                continue # failed, leave in queue for next time
                        else:
                            if setMoviesSeenOnTrakt([movie.traktise()]) is None:
                                continue # failed, leave in queue for next time
                elif change['subject'] == 'watchingStatus':
                    if change['remoteId'] in trakt_cache._movies and '_watchingStatus' in trakt_cache._movies[change['remoteId']]:
                        movie = trakt_cache._movies[change['remoteId']]
                        if change['value'] == True:
                            if watchingMovieOnTrakt(movie.traktise()) is None:
                                continue # failed, leave in queue for next time
                        else:
                            if cancelWatchingMovieOnTrakt() is None:
                                continue # failed, leave in queue for next time
                elif change['subject'] == 'libraryStatus':
                    if change['value'] == True:
                        if addMoviesToTraktCollection([Movie(change['remoteId']).traktise()]) is None:
                            continue # failed, leave in queue for next time
                    else:
                        result = removeMoviesFromTraktCollection([Movie(change['remoteId']).traktise()], returnStatus = True)
                        Debug('[TraktCache] _updateTrakt, libraryStatus, unlibrary, responce: '+str(result))
                        if 'error' in result: continue # failed, leave in queue for next time
                        
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
    trakt_cache._updateCache(cacheChanges, traktData)

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
        movieAttributes = ['title', 'year', 'runtime', 'released', 'tagline', 'overview', 'certification', 'playcount', 'rating', 'watchlistStatus', 'recommendedStatus', 'libraryStatus', 'trailer', 'poster', 'fanart']
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
        if remoteId is None: continue
        if remoteId[0] == '_': continue
        newItem = newer[remoteId]
        if newItem['_remoteId'] not in older:
            if xbmc: changes.append({'remoteId': remoteId, 'subject': 'libraryStatus', 'value':True})
            for attribute in attributes:
                if newItem['_'+attribute] is not None: changes.append({'remoteId': remoteId, 'subject': attribute, 'value':newItem['_'+attribute]})
    
    for remoteId in older:
        if remoteId[0] == '_': continue
        oldItem = older[remoteId]
        if oldItem is None:
            del older[remoteId]
            continue
        if remoteId not in newer: #If item not in library
            if xbmc:
                if oldItem._libraryStatus: #If item had been in library
                    changes.append({'remoteId': remoteId, 'subject': 'libraryStatus', 'value':False})
        else:
            newItem = newer[remoteId]
            if newItem is None:
                del newer[remoteId]
                continue
            for attribute in attributes:
                if newItem['_'+attribute] <> oldItem['_'+attribute]: # If the non cached data is different from the old data cached locally
                    if newItem['_'+attribute] is not None: changes.append({'remoteId': remoteId, 'subject': attribute, 'value':newItem['_'+attribute]})
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

def updateSyncTimes(sets = [], remoteIds = []):
    updated = {}
    for set in sets: updated[str(set)] = None
    if 'all' in updated:
        updated['all'] = True
        updated['movieall'] = True
    if 'movieall' in updated:
        updated['movielibrary'] = True
        updated['movierecommended'] = True
        updated['moviewatchlist'] = True
        updated['movieimages'] = True
    if 'library' in updated:
        updated['movielibrary'] = True
    
    syncTimes = {'moviewatchlist': 10*60,
                 'movierecommended': 30*60,
                 'movielibrary': 6*60*60,
                 'movieimages': 6*60*60,
                 'movieall': 24*60*60,
                 'library': 60*60,
                 'all': 24*60*60}
    for set in updated:
        if set not in syncTimes:
            Debug("[TraktCache] Tried to bump update time of unknown update set:" +set)
            continue
        trakt_cache._expire[set] = time.time() + syncTimes[set]
    for remoteId in remoteIds:
        trakt_cache._expire[remoteId] = time.time() + 10*60 # +10mins

def needSyncAtLeast(sets = [], remoteIds = [], force = False):
    # This function should block untill all syncs have been satisfied
    staleSets = {}
    for set in sets:
        Debug("[~] "+repr(set))
        staleSets[str(set)] = None
    if 'library' in  staleSets:
        if 'movielibrary' in staleSets: del staleSets['movielibrary']
    if 'movieall' in staleSets:
        if 'movielibrary' in staleSets: del staleSets['movielibrary']
        if 'movierecommended' in staleSets: del staleSets['movierecommended']
        if 'moviewatchlist' in staleSets: del staleSets['moviewatchlist']
        if 'movieimages' in staleSets: del staleSets['movieimages']
    if 'all' in staleSets:
        if 'movieall' in staleSets: del staleSets['movieall']
    for set in staleSets:
        if set not in trakt_cache._expire or trakt_cache._expire[set] < time.time() or force:
            refreshSet(set)
    for remoteId in remoteIds:
        if remoteId not in trakt_cache._expire or trakt_cache._expire[remoteId] < time.time():
            refreshItem(remoteId)
    return
    
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

def refreshSet(set):
    try:
        _refresh[set]()
    except KeyError:
        Debug("[TraktCache] No method specified to refresh the set: "+str(set))

def refreshItem(remoteId):
    if remoteId.partition("=") in ('imdb', 'tmdb'):
        refreshMovie(remoteId)
    else:
        Debug("[TraktCache] No method yet to refresh non-movie items")
        
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
    needSyncAtLeast(['moviewatchlist'])
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
    Debug("[TraktCache] Refreshing watchlist")
    traktWatchlist = getWatchlistMoviesFromTrakt()
    watchlist = {}
    traktData = {}
    traktData['movies'] = []
    for movie in traktWatchlist:
        localMovie = Movie.fromTrakt(movie)
        watchlist[localMovie['_remoteId']] = localMovie
    traktData['movies'] = watchlist
    _sync(traktData = traktData)
    for remoteId in trakt_cache._movies:
        if remoteId[0] == '_': continue
        movie = trakt_cache._movies[remoteId]
        if movie is None:
            del trakt_cache._movies[remoteId]
            continue
        if movie['_watchlistStatus'] <> (remoteId in watchlist):
            movie['_watchlistStatus'] = not movie['_watchlistStatus']
            trakt_cache._movies[movie['_remoteId']] = movie
            
    updateSyncTimes(['moviewatchlist'], watchlist.keys())
    
_refresh = {}
_refresh['library'] = refreshLibrary
_refresh['moviewatchlist'] = refreshMovieWatchlist
