# -*- coding: utf-8 -*-
# 

import xbmc,xbmcaddon
from utilities import *
from movie import *
import time
import shelve
from threading import Lock, Semaphore
import trakt_cache

__author__ = "Ralph-Gordon Paul, Adrian Cowan"
__credits__ = ["Ralph-Gordon Paul", "Adrian Cowan", "Justin Nemeth",  "Sean Rudford"]
__license__ = "GPL"
__maintainer__ = "Ralph-Gordon Paul"
__email__ = "ralph-gordon.paul@uni-duesseldorf.de"
__status__ = "Production"

__settings__ = xbmcaddon.Addon( "script.TraktUtilities" )
__language__ = __settings__.getLocalizedString
username = __settings__.getSetting("username")

# Caches all information between the add-on and the web based trakt api

_location = None

class SafeShelf:
    __writeMutex = {}
    __readMutex = {}
    __readCount = {}
    __shelf = {}
    
    def __init__(self, name, writeable = False):
        self.name = name
        self.writeable = writeable
        
    @staticmethod
    def set(name, shelf):
        SafeShelf.__shelf[name] = shelf
        SafeShelf.__writeMutex[name] = Lock()
        SafeShelf.__readMutex[name] = Lock()
        SafeShelf.__readCount[name] = 0
    
    def __enter__(self):
        if self.writeable:
            if self.name not in SafeShelf.__shelf:
                SafeShelf.__shelf[self.name] = None
                SafeShelf.__writeMutex[self.name] = Lock()
                SafeShelf.__readMutex[self.name] = Lock()
                SafeShelf.__readCount[self.name] = 0
            with SafeShelf.__readMutex[self.name]:
                SafeShelf.__writeMutex[self.name].acquire()
            return SafeShelf.__shelf[self.name]
        else:
            if self.name not in SafeShelf.__shelf:
                raise NameError("Shelf "+repr(self.name)+" is not defined")
            with SafeShelf.__writeMutex[self.name]:
                if SafeShelf.__readCount[self.name] == 0:
                    SafeShelf.__readMutex[self.name].acquire()
                SafeShelf.__readCount[self.name] += 1
            return SafeShelf.__shelf[self.name]
        
    def __exit__(self, type, value, traceback):
        if self.writeable:
            with SafeShelf.__readMutex[self.name]:
                SafeShelf.__writeMutex[self.name].release()
        else:
            with SafeShelf.__writeMutex[self.name]:
                SafeShelf.__readCount[self.name] -= 1
                if SafeShelf.__readCount[self.name] == 0:
                    SafeShelf.__readMutex[self.name].release()
        
def init(location=None):
    trakt_cache._location = xbmc.translatePath(location)
    if trakt_cache._location is not None:
        _fill()

def _fill():
    SafeShelf.set("movies", shelve.open(trakt_cache._location+".movies"))
    SafeShelf.set("shows", shelve.open(trakt_cache._location+".shows"))
    SafeShelf.set("episodes", shelve.open(trakt_cache._location+".episodes"))
    SafeShelf.set("expire", shelve.open(trakt_cache._location+".ttl"))
    
def _sync(xbmcData = None, traktData = None, cacheData = None):
    Debug("[TraktCache] Syncronising")
    
    if xbmcData is not None and 'movies' not in xbmcData: xbmcData['movies'] = {}
    if traktData is not None and 'movies' not in traktData: traktData['movies'] = {}
    if cacheData is not None and 'movies' not in cacheData: cacheData['movies'] = {}
    if xbmcData is not None and 'shows' not in xbmcData: xbmcData['shows'] = {}
    if traktData is not None and 'shows' not in traktData: traktData['shows'] = {}
    if cacheData is not None and 'shows' not in cacheData: cacheData['shows'] = {}
    if xbmcData is not None and 'episodes' not in xbmcData: xbmcData['episodes'] = {}
    if traktData is not None and 'episodes' not in traktData: traktData['episodes'] = {}
    if cacheData is not None and 'episodes' not in cacheData: cacheData['episodes'] = {}
    
    # Find and list all changes
    if traktData is not None:
        xbmcChanges = trakt_cache._syncCompare(traktData, cache = cacheData)
        Debug("[~] X"+repr(xbmcChanges))
    if xbmcData is not None:
        traktChanges = trakt_cache._syncCompare(xbmcData, xbmc = True, cache = cacheData)
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
                        if (xbmcChange['value'] <> traktChange['value']):
                            Debug("[~] t"+repr(traktChange))
                            Debug("[~] x"+repr(xbmcChange))
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
    # Collate list of updated items
    remoteIds = []
    if traktData is not None:
        for type in ['movies', 'shows', 'episodes']:
            for remoteId in traktData[type]:
                remoteIds.append(remoteId)
    if xbmcData is not None:
        for type in ['movies', 'shows', 'episodes']:
            for remoteId in xbmcData[type]:
                remoteIds.append(remoteId)
    # Update next sync times
    trakt_cache.updateSyncTimes(['library'], remoteIds)

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
                if change['subject'] in ('title', 'year', 'runtime', 'released', 'tagline', 'overview', 'classification', 'playcount', 'rating', 'watchlistStatus', 'recommendedStatus', 'libraryStatus', 'trailer', 'poster', 'fanart'):
                    with SafeShelf('movies') as movies:
                        exists = change['remoteId'] in movies
                        if exists:
                            movie = movies[change['remoteId']]
                    if exists:
                        movie = movies[change['remoteId']]
                        
                        Debug("[TraktCache] Updating "+unicode(movie)+", setting "+str(change['subject'])+" to "+unicode(change['value']))
                        movie['_'+change['subject']] = change['value']
                        if 'bestBefore' in change:
                            movie._bestBefore[change['subject']] = change['bestBefore']
                        with SafeShelf('movies', True) as movies:
                            movies[change['remoteId']] = movie
                    else:
                        if 'movies' in traktData and change['remoteId'] in traktData['movies']:
                            Debug("[TraktCache] Inserting into cache from local trakt data: "+repr(traktData['movies'][change['remoteId']]))
                            with SafeShelf('movies', True) as movies:
                                movies[change['remoteId']] = traktData['movies'][change['remoteId']]
                        else:
                            Debug("[TraktCache] Inserting into cache from remote trakt data")
                            movie = Movie.download(change['remoteId'])
                            if movie is not None:
                                movie.save()

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
                elif change['subject'] in ('title', 'year', 'runtime', 'released', 'tagline', 'overview', 'classification', 'rating', 'watchlistStatus', 'recommendedStatus', 'libraryStatus', 'trailer', 'poster', 'fanart'):
                    # ignore, irrelevant, pass on to update the cache
                    pass
                else:
                    # invalid
                    continue
                # succeeded
                cacheChanges['movies'].append(change)
    _updateCache(cacheChanges, traktData)        

def _updateTrakt(newChanges = None, traktData = {}):
    changeQueue = {}
    with SafeShelf('movies') as movies:
        if '_queue' in movies:
            changeQueue['movies'] = movies['_queue']
        else:
            changeQueue['movies'] = []
        
    with SafeShelf('shows') as shows:
        if '_queue' in shows:
            changeQueue['shows'] = shows['_queue']
        else:
            changeQueue['shows'] = []
            
    with SafeShelf('episodes') as episodes:
        if '_queue' in episodes:
            changeQueue['episodes'] = episodes['_queue']
        else:
            changeQueue['episodes'] = []
    
    if newChanges is not None:
        if 'movies' in newChanges:
            # Add and new changes to the queue
            for change in newChanges['movies']:
                if change not in changeQueue['movies']: # Check that we arn't adding duplicates
                    changeQueue['movies'].append(change)
            
            with SafeShelf('movies', True) as movies:
                movies['_queue'] = changeQueue['movies']
    
    cacheChanges = {}
    
    Debug("[~] CQ: "+repr(changeQueue))
    if 'movies' in changeQueue:
        cacheChanges['movies'] = []
        for change in changeQueue['movies']:
            Debug("[TraktCache] trakt update: "+repr(change))
            if 'remoteId' in change and 'subject' in change and 'value' in change:
                if change['subject'] == 'watchlistStatus':
                    if change['value'] == True:
                        if addMoviesToWatchlist([Movie(change['remoteId']).traktise()]) is None:
                            continue # failed, leave in queue for next time
                    else:
                        if removeMoviesFromWatchlist([Movie(change['remoteId']).traktise()]) is None:
                            continue # failed, leave in queue for next time
                elif change['subject'] == 'playcount':
                    movie = Movie(change['remoteId'])
                    movie._playcount = change['value']
                    if (movie._playcount >= 0):
                        if (movie._playcount == 0):
                            if Trakt.movieUnseen([movie.traktise()]) is None:
                                continue # failed, leave in queue for next time
                        else:
                            if Trakt.movieSeen([movie.traktise()]) is None:
                                continue # failed, leave in queue for next time
                elif change['subject'] == 'libraryStatus':
                    if change['value'] == True:
                        if Trakt.movieLibrary([Movie(change['remoteId']).traktise()]) is None:
                            continue # failed, leave in queue for next time
                    else:
                        result = Trakt.movieUnlibrary([Movie(change['remoteId']).traktise()], returnStatus = True)
                        Debug('[TraktCache] _updateTrakt, libraryStatus, unlibrary, responce: '+str(result))
                        if 'error' in result: continue # failed, leave in queue for next time
                elif change['subject'] == 'rating':
                    if rateMovieOnTrakt(Movie(change['remoteId']).traktise(), change['value']) is None:
                        continue # failed, leave in queue for next time
                elif change['subject'] in ('title', 'year', 'runtime', 'released', 'tagline', 'overview', 'classification', 'rating', 'trailer', 'poster', 'fanart'):
                    # ignore, irrelevant, pass on to update the cache
                    pass
                else:
                    # invalid
                    with SafeShelf('movies', True) as movies:
                        queue = movies['_queue']
                        queue.remove(change)
                        movies['_queue'] = queue
                    continue
                # succeeded
                cacheChanges['movies'].append(change)
            # either succeeded or invalid
            with SafeShelf('movies', True) as movies:
                queue = movies['_queue']
                queue.remove(change)
                movies['_queue'] = queue
    trakt_cache._updateCache(cacheChanges, traktData)

def _copyTrakt():
    traktData = {}
    
    movies = {}
    traktMovies = Trakt.userLibraryMoviesAll(username, daemon=True)
    watchlistMovies = traktMovieListByImdbID(Trakt.userWatchlistMovies(username))
    for movie in traktMovies:
        local = Movie.fromTrakt(movie)
        if local is None:
            continue
        if 'imdb_id' in movie:
            local._watchlistStatus = movie['imdb_id'] in watchlistMovies
        movies[local._remoteId] = local
        
    
    shows = {}
    #traktShows = Trakt.userLibraryShowsAll(daemon=True)
    #for show in traktShows:
    #    shows.append(Show.fromTrakt(show))
        
    episodes = {}
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
    
    shows = {}
    #traktShows = Trakt.userLibraryShowsAll(daemon=True)
    #for show in traktShows:
    #    shows.append(Show.fromTrakt(show))
        
    episodes = {}
    #traktEpisodes = getEpisodesFromTrakt(daemon=True)
    #for episode in traktEpisodes:
    #    episodes.append(Episode.fromTrakt(episode))
        
    xbmcData['movies'] = movies
    xbmcData['shows'] = shows
    xbmcData['episodes'] = episodes
    return xbmcData

attributes = {
    'xbmc': {
        'movies': {
            'primary': ['playcount'],
            'secondary': ['title', 'year', 'runtime']
        },
        'shows': {
            'primary': [],
            'secondary': []
        },
        'episodes': {
            'primary': ['playcount'],
            'secondary': []
        }
    },
    'trakt': {
        'movies': {
            'primary': ['title', 'year', 'runtime', 'released', 'tagline', 'overview', 'classification', 'playcount', 'rating', 'watchlistStatus', 'recommendedStatus', 'libraryStatus'],
            'secondary': ['trailer', 'poster', 'fanart']
        },
        'shows': {
            'primary': ['rating', 'watchlistStatus', 'recommendedStatus'],
            'secondary': []
        },
        'episodes': {
            'primary': ['playcount', 'rating', 'watchlistStatus', 'libraryStatus'],
            'secondary': []
        }
    }
}

def _syncCompare(data, xbmc = False, cache = None):
    if xbmc:
        attr = attributes['xbmc']
    else :
        attr = attributes['trakt']
    changes = {}
    
    if cache is None:
        # Compare movies
        with SafeShelf('movies', True) as movies:
            changes['movies'] = _listChanges(data['movies'], movies, attr['movies']['primary'],  attr['movies']['secondary'], xbmc, writeBack = None)
        # Compare TV shows
        with SafeShelf('shows', True) as shows:
            changes['shows'] = _listChanges(data['shows'], shows, attr['shows']['primary'],  attr['shows']['secondary'], xbmc, writeBack = None)
        # Compare TV episodes
        with SafeShelf('episodes', True) as episodes:
            changes['episodes'] = _listChanges(data['episodes'], episodes, attr['episodes']['primary'],  attr['episodes']['secondary'], xbmc, writeBack = None)
    else:
        # Compare movies
        with SafeShelf('movies', True) as movies:
            changes['movies'] = _listChanges(data['movies'], cache['movies'], attr['movies']['primary'],  attr['movies']['secondary'], xbmc, writeBack = movies)
        # Compare TV shows
        with SafeShelf('shows', True) as shows:
            changes['shows'] = _listChanges(data['shows'], cache['shows'], attr['shows']['primary'],  attr['shows']['secondary'], xbmc, writeBack = shows)
        # Compare TV episodes
        with SafeShelf('episodes', True) as episodes:
            changes['episodes'] = _listChanges(data['episodes'], cache['episodes'], attr['episodes']['primary'],  attr['episodes']['secondary'], xbmc, writeBack = episodes)
    return changes

def _listChanges(newer, older, attributes, weakAttributes, xbmc = False, writeBack = False):
    changes = []
    # Find new items
    for remoteId in newer:
        if remoteId is None: continue
        if remoteId[0] == '_': continue
        newItem = newer[remoteId]
        if newItem['_remoteId'] not in older:
            if xbmc: changes.append({'remoteId': remoteId, 'subject': 'libraryStatus', 'value':True})
            for attribute in attributes:
                if newItem['_'+attribute] is not None: changes.append({'remoteId': remoteId, 'subject': attribute, 'value':newItem['_'+attribute], 'bestBefore': time.time()+24*60*60})
            for attribute in weakAttributes:
                if newItem['_'+attribute] is not None: changes.append({'remoteId': remoteId, 'subject': attribute, 'value':newItem['_'+attribute], 'bestBefore': time.time()+24*60*60})
    
    for remoteId in older:
        if remoteId[0] == '_': continue
        oldItem = older[remoteId]
        if oldItem is None:
            continue
        if remoteId not in newer: #If item not in library
            if xbmc:
                if oldItem._libraryStatus: #If item had been in library
                    changes.append({'remoteId': remoteId, 'subject': 'libraryStatus', 'value':False})
        else:
            newItem = newer[remoteId]
            if newItem is None:
                continue
            for attribute in attributes:
                if newItem['_'+attribute] <> oldItem['_'+attribute]: # If the non cached data is different from the old data cached locally
                    if newItem['_'+attribute] is not None: changes.append({'remoteId': remoteId, 'subject': attribute, 'value':newItem['_'+attribute]})
                oldItem._bestBefore[attribute] = time.time()+24*60*60
            for attribute in weakAttributes:
                if oldItem['_'+attribute] is None: # If the non cached data is different from the old data cached locally
                    if newItem['_'+attribute] is not None: changes.append({'remoteId': remoteId, 'subject': attribute, 'value':newItem['_'+attribute]})
                oldItem._bestBefore[attribute] = time.time()+24*60*60
        oldItem._bestBefore['libraryStatus'] = time.time()+12*60*60
        if writeBack is None:
            older[remoteId] = oldItem
        elif writeBack == False:
            pass
        else:
            writeBack[remoteId] = oldItem
    return changes

def makeChanges(changes, traktOnly = False, xbmcOnly = False):
    Debug("[~] Made changes: "+repr(changes))
    if not traktOnly: _updateXbmc(changes)
    if not xbmcOnly: _updateTrakt(changes)
    
def relateMovieId(localId, remoteId):
    with SafeShelf('movies', True) as movies:
        if '_byLocalId' in movies:
            index = movies['_byLocalId']
        else:
            index = {}
        index[localId] = remoteId
        movies['_byLocalId'] = index
    
def getMovieRemoteId(localId):
    with SafeShelf('movies') as movies:
        if '_byLocalId' in movies and localId in movies['_byLocalId']:
            return movies['_byLocalId'][localId]
    return None

def getMovieLocalIds(remoteId):
    hits = []
    with SafeShelf('movies') as movies:
        for localId in movies['_byLocalId']:
            if remoteId == movies['_byLocalId'][localId]:
                hits.append(localId)
    return hits

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
    if 'movielibrary' in updated:
        updated['movieseen'] = True
        
    syncTimes = {'moviewatchlist': 10*60,
                 'movierecommended': 30*60,
                 'movieseen': 3*60*60,
                 'movielibrary': 6*60*60,
                 'movieimages': 6*60*60,
                 'movieall': 24*60*60,
                 'library': 60*60,
                 'all': 24*60*60}
    with SafeShelf('expire', True) as expire:
        for set in updated:
            if set not in syncTimes:
                Debug("[TraktCache] Tried to bump update time of unknown update set:" +set)
                continue
            expire[set] = time.time() + syncTimes[set]
        for remoteId in remoteIds:
            expire[remoteId] = time.time() + 10*60 # +10mins

def needSyncAtLeast(sets = [], remoteIds = [], force = False):
    # This function should block untill all syncs have been satisfied
    staleSets = {}
    for set in sets:
            staleSets[str(set)] = None
    if 'library' in  staleSets:
        if 'movielibrary' in staleSets: del staleSets['movielibrary']
        if 'movieseen' in staleSets: del staleSets['movieseen']
    if 'movielibrary' in  staleSets:
        if 'movieseen' in staleSets: del staleSets['movieseen']
    if 'movieall' in staleSets:
        if 'movielibrary' in staleSets: del staleSets['movielibrary']
        if 'movieseen' in staleSets: del staleSets['movieseen']
        if 'movierecommended' in staleSets: del staleSets['movierecommended']
        if 'moviewatchlist' in staleSets: del staleSets['moviewatchlist']
        if 'movieimages' in staleSets: del staleSets['movieimages']
    if 'all' in staleSets:
        if 'movieall' in staleSets: del staleSets['movieall']
    for set in staleSets:
        with SafeShelf('expire') as expire:
            stale = set not in expire or expire[set] < time.time() or force
        if stale:
            refreshSet(set)
    for remoteId in remoteIds:
        with SafeShelf('expire') as expire:
            stale = remoteId not in expire or expire[remoteId] < time.time() or force
        if stale:
            refreshItem(remoteId)
    return
    
def getMovie(remoteId = None, localId = None):
    if remoteId is None and localId is None:
        raise ValueError("Must provide at least one form of id")
    if remoteId is None:
        remoteId = trakt_cache.getMovieRemoteId(localId)
    if remoteId is None:
        return None
    needSyncAtLeast(remoteIds = [remoteId])
    with SafeShelf('movies') as movies:
        if remoteId not in movies:
            raise "Bad, logic bomb"
        return movies[remoteId]
        

def refreshSet(set):
    try:
        method = _refresh[set]
    except KeyError:
        Debug("[TraktCache] No method specified to refresh the set: "+str(set))
    else:
        method()

def refreshItem(remoteId):
    Debug("[~] "+repr(remoteId.partition("=")[0]))
    if remoteId.partition("=")[0] in ('imdb', 'tmdb'):
        refreshMovie(remoteId)
    else:
        Debug("[TraktCache] No method yet to refresh non-movie items")
        
def refreshMovie(remoteId, property = None):
    localIds = getMovieLocalIds(remoteId)
    if len(localIds) == 0:
        localId = None
    else:
        localId  = localIds[0]
    xbmcData = None
    cacheData = None
    if localId is not None:
        xbmcData = {'movies': {remoteId: Movie.fromXbmc(getMovieDetailsFromXbmc(localId,['title', 'year', 'originaltitle', 'imdbnumber', 'playcount', 'lastplayed', 'runtime']))}}
    if property is not None:
        if property in ('title', 'year', 'runtime', 'released', 'tagline', 'overview', 'classification', 'playcount', 'rating', 'watchlistStatus', 'libraryStatus', 'traktDbStatus', 'trailer', 'poster', 'fanart'):
            traktData = {'movies': {remoteId: Movie.download(remoteId)}}
        elif property in ('recommendedStatus'):
            refreshRecommendedMovies()
            return
    else:
        traktData = {'movies': {remoteId: Movie.download(remoteId)}}
    with SafeShelf('movies') as movies:
        if remoteId in movies:
            cacheData = {'movies': {remoteId: movies[remoteId]}}
            
    _sync(xbmcData, traktData, cacheData)
    
    with SafeShelf('expire', True) as expire:
        expire[remoteId] = time.time() + 10*60 # +10mins

def saveMovie(movie):
    with SafeShelf('movies', True) as movies:
        movies[movie.remoteId] = movie


def getMovieWatchList():
    needSyncAtLeast(['moviewatchlist'])
    watchlist = []
    with SafeShelf('movies') as movies:
        for remoteId in movies:
            if remoteId[0] == '_': continue
            movie = movies[remoteId]
            if movie is None:
                continue
            if movie['_watchlistStatus'] == True:
                watchlist.append(movie)
    return watchlist


def refreshMovieWatchlist():
    Debug("[TraktCache] Refreshing watchlist")
    traktWatchlist = Trakt.userWatchlistMovies(username)
    watchlist = {}
    traktData = {}
    traktData['movies'] = []
    for movie in traktWatchlist:
        localMovie = Movie.fromTrakt(movie)
        watchlist[localMovie['_remoteId']] = localMovie
    traktData['movies'] = watchlist
    _sync(traktData = traktData)
    with SafeShelf('movies', True) as movies:
        for remoteId in movies:
            if remoteId[0] == '_': continue
            movie = movies[remoteId]
            if movie is None:
                continue
            if movie['_watchlistStatus'] <> (remoteId in watchlist):
                movie['_watchlistStatus'] = not movie['_watchlistStatus']
                movies[movie['_remoteId']] = movie
            
    updateSyncTimes(['moviewatchlist'], watchlist.keys())
    
def getRecommendedMovies():
    needSyncAtLeast(['movierecommended'])
    items = []
    with SafeShelf('movies') as movies:
        for remoteId in movies:
            if remoteId[0] == '_': continue
            movie = movies[remoteId]
            if movie is None:
                continue
            if movie['_recommendedStatus'] == True:
                items.append(movie)
    return items


def refreshRecommendedMovies():
    Debug("[TraktCache] Refreshing recommended movies")
    traktItems = Trakt.recommendationsMovies()
    items = {}
    traktData = {}
    traktData['movies'] = []
    for movie in traktItems:
        localMovie = Movie.fromTrakt(movie)
        items[localMovie['_remoteId']] = localMovie
    traktData['movies'] = items
    _sync(traktData = traktData)
    with SafeShelf('movies', True) as movies:
        for remoteId in movies:
            if remoteId[0] == '_': continue
            movie = movies[remoteId]
            if movie is None:
                continue
            status = remoteId in items;
            if movie['_recommendedStatus'] <> True and status:
                movie['_recommendedStatus'] = True
                movies[movie['_remoteId']] = movie
            elif movie['_recommendedStatus'] <> False and not status:
                movie['_recommendedStatus'] = False
                movies[movie['_remoteId']] = movie
            
    updateSyncTimes(['movierecommended'], items.keys())
    
def getTrendingMovies():
    traktItems = Trakt.moviesTrending();
    items = []
    for movie in traktItems:
        localMovie = Movie.fromTrakt(movie, static = True)
        items.append(localMovie)
    return items

_refresh = {}
_refresh['library'] = refreshLibrary
_refresh['moviewatchlist'] = refreshMovieWatchlist
_refresh['movierecommended'] = refreshRecommendedMovies
