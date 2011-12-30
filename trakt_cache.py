# -*- coding: utf-8 -*-
# 

import xbmc,xbmcaddon
from utilities import *
from movie import Movie
from show import Show
from episode import Episode
import time
import shelve
import trakt_cache
from safeShelf import SafeShelf
from async_tools import Pool, AsyncCall, async

__author__ = "Ralph-Gordon Paul, Adrian Cowan"
__credits__ = ["Ralph-Gordon Paul", "Adrian Cowan", "Justin Nemeth",  "Sean Rudford"]
__license__ = "GPL"
__maintainer__ = "Ralph-Gordon Paul"
__email__ = "ralph-gordon.paul@uni-duesseldorf.de"
__status__ = "Production"

__settings__ = xbmcaddon.Addon( "script.TraktUtilities" )
__language__ = __settings__.getLocalizedString
username = __settings__.getSetting("username")

###################
# Caches all information between the add-on and the web based trakt api
#
# trakt_cache is a group of functions that organise and maintain the cached information between xbmcs DB and the one at
# trakt.tv. It is based on the rational that you only want to keep certain peices of information up to date but that you
# might want it again soon and there is no point in going and getting it all over again.
#
# Information is stored in a DB file in the filesystem using 'shelfs'. To make these safe for using in theaded programs
# the SafeShelf class has been created, this allows multiple reads simultaniously but locks the whole db down for
# writes.
#
# Access for reading is like this:
#     with SafeShelf('movies') as movies:
#         #Do stuff with the DB
#         foo = movies['bar']
#
# Access for writing is like this:
#     with SafeShelf('movies', True) as movies:
#         #Do stuff with the DB
#         movies['foo'] = bar
#
# Internally the caching is based on sets and items, a set is a list of items, like the watchlist or the recommended
# movies list. Each set has an associated refresher function unless it is not cached (like the trending lists).
#
# When any request is make for a set or information from an item a check is performed to make sure that the information
# is as recent as it required, and if it is not the associated refresher is executed to get newer information.
#
# Internally to find the changes between the new copys of the items and the old ones a generalised comparitor is
# provided, this has a list of known variables to look for changes in.
#
# Basic operation of trakt_cache starts with:
#     trakt_cache.init("the/path/to/the/dbs/and/the/common/part/of/the/db/name")
# 
# From this point any requests for data with a function like:
#     trakt_cache.getMovieLibrary()
# or the more abstracted:
#     sets.Movies.library()
# will return information that is up to date within internally defined standards
##

_location = None
  
##
# Cache DB operations
##

def init(location=None):
    trakt_cache._location = xbmc.translatePath(location)
    if trakt_cache._location is not None:
        _fill()
def _fill():
    SafeShelf.set('movies', shelve.open(trakt_cache._location+".movies"))
    SafeShelf.set('shows', shelve.open(trakt_cache._location+".shows"))
    SafeShelf.set('episodes', shelve.open(trakt_cache._location+".episodes"))
    SafeShelf.set('expire', shelve.open(trakt_cache._location+".ttl"))
    
def _sync(xbmcData = None, traktData = None, cacheData = None):
    Debug("[TraktCache] Syncronising")
    
    if xbmcData is not None and ('movies' not in xbmcData or xbmcData['movies'] is None): xbmcData['movies'] = {}
    if traktData is not None and ('movies' not in traktData or traktData['movies'] is None): traktData['movies'] = {}
    if cacheData is not None and ('movies' not in cacheData or cacheData['movies'] is None): cacheData['movies'] = {}
    if xbmcData is not None and ('shows' not in xbmcData or xbmcData['shows'] is None): xbmcData['shows'] = {}
    if traktData is not None and ('shows' not in traktData or traktData['shows'] is None): traktData['shows'] = {}
    if cacheData is not None and ('shows' not in cacheData or cacheData['shows'] is None): cacheData['shows'] = {}
    if xbmcData is not None and ('episodes' not in xbmcData or xbmcData['episodes'] is None): xbmcData['episodes'] = {}
    if traktData is not None and ('episodes' not in traktData or traktData['episodes'] is None): traktData['episodes'] = {}
    if cacheData is not None and ('episodes' not in cacheData or cacheData['episodes'] is None): cacheData['episodes'] = {}
    
    #isolation testing
    #isolatedId = 'tvdb=76107@21x15'
    """if xbmcData is not None:
        xbmcData['movies'] = {}
        xbmcData['shows'] = {}
        if isolatedId in xbmcData['episodes']:
            xbmcData['episodes'] = {isolatedId: xbmcData['episodes'][isolatedId]}
        else:
            xbmcData['episodes'] = {}
    if traktData is not None:
        traktData['movies'] = {}
        traktData['shows'] = {}
        if isolatedId in traktData['episodes']:
            traktData['episodes'] = {isolatedId: traktData['episodes'][isolatedId]}
        else:
            traktData['episodes'] = {}"""
    
    
    # Find and list all changes
    if traktData is not None:
        xbmcChanges = trakt_cache._syncCompare(traktData, cache = cacheData)
        #for item in xbmcChanges['episodes']:
        #    if item['remoteId'] == isolatedId:
        #        Debug("[~] X"+repr(item))
    if xbmcData is not None:
        traktChanges = trakt_cache._syncCompare(xbmcData, xbmc = True, cache = cacheData)
        #for item in traktChanges['episodes']:
        #    if item['remoteId'] == isolatedId:
        #        Debug("[~] T"+repr(item))
        
    # Find unanimous changes and direct them to the cache
    cacheChanges = {}
    cacheChanges['movies'] = []
    cacheChanges['shows'] = []
    cacheChanges['episodes'] = []
    
    if traktData is not None and xbmcData is not None:
        for type in ['movies', 'shows', 'episodes']:
            removeListT = []
            removeListX = []
            for xbmcChange in xbmcChanges[type]:
                for traktChange in traktChanges[type]: # I think this works, but my concern is that it wont compare the values
                    if (xbmcChange['remoteId'] == traktChange['remoteId'] and xbmcChange['subject'] == traktChange['subject']):
                        removeListT.append(traktChange)
                        removeListX.append(xbmcChange)
                        if (xbmcChange['value'] <> traktChange['value']):
                            #Debug("[~] t"+repr(traktChange))
                            #Debug("[~] x"+repr(xbmcChange))
                            winingChange = traktChange
                            if 'weak' in winingChange: winingChange['weak'] = False
                            if xbmcChange['subject'] in ('playcount'):
                                if xbmcChange['value']>traktChange['value']:
                                    winingChange['value'] = xbmcChange['value']
                                else:
                                    winingChange['value'] = traktChange['value']
                            elif xbmcChange['subject'] in ('libraryStatus'):
                                winingChange['value'] = xbmcChange['value'] or traktChange['value']
                            cacheChanges[type].append(winingChange)
                        else:
                            cacheChanges[type].append(traktChange)
            for item in removeListT:
                try:
                    traktChanges[type].remove(item)   
                except ValueError:
                    continue
            for item in removeListX:
                try:
                    xbmcChanges[type].remove(item)
                except ValueError:
                    continue
    if traktData is not None:
        for type in ['movies', 'shows', 'episodes']:
            moveList = []
            for xbmcChange in xbmcChanges[type]:
                if 'weak' in xbmcChange and xbmcChange['weak']:
                    moveList.append(xbmcChange)
            for item in moveList:
                xbmcChanges[type].remove(item)
                cacheChanges[type].append(item)
    if xbmcData is not None:
        for type in ['movies', 'shows', 'episodes']:
            moveList = []
            for traktChange in traktChanges[type]:
                if 'weak' in traktChange and traktChange['weak']:
                    moveList.append(traktChange)
            for item in moveList:
                traktChanges[type].remove(item)
                cacheChanges[type].append(item)
    
    """if traktData is not None:
        for item in xbmcChanges['episodes']:
            if item['remoteId'] == isolatedId:
                Debug("[~] X"+repr(item))
    if xbmcData is not None:
        for item in traktChanges['episodes']:
            if item['remoteId'] == isolatedId:
                Debug("[~] T"+repr(item))
    for item in cacheChanges['episodes']:
        if item['remoteId'] == isolatedId:
            Debug("[~] C"+repr(item))"""
                    
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
    ## Update next sync times
    #trakt_cache.updateSyncTimes(['library'], remoteIds)
    
##
# DB updaters
##

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
                            movie = traktData['movies'][change['remoteId']]
                            if movie is not None:
                                movie.save()
                        else:
                            Debug("[TraktCache] Inserting into cache from remote trakt data")
                            movie = Movie.download(change['remoteId'])
                            if movie is not None:
                                movie.save()
    if 'shows' in changes:
        for change in changes['shows']:
            Debug("[TraktCache] Cache update: "+repr(change))
            if 'remoteId' in change and 'subject' in change and 'value' in change:
                if change['subject'] in ('title', 'year', 'firstAired', 'country', 'overview', 'runtime', 'network', 'airDay', 'airTime', 'classification', 'rating', 'watchlistStatus', 'recommendedStatus', 'libraryStatus', 'poster', 'fanart', 'episodes'):
                    with SafeShelf('shows') as shows:
                        exists = change['remoteId'] in shows
                        if exists:
                            show = shows[change['remoteId']]
                    if exists:
                        show = shows[change['remoteId']]
                        
                        Debug("[TraktCache] Updating "+unicode(show)+", setting "+str(change['subject'])+" to "+unicode(change['value']))
                        show['_'+change['subject']] = change['value']
                        if 'bestBefore' in change:
                            show._bestBefore[change['subject']] = change['bestBefore']
                        with SafeShelf('shows', True) as shows:
                            shows[change['remoteId']] = show
                    else:
                        if 'shows' in traktData and change['remoteId'] in traktData['shows']:
                            Debug("[TraktCache] Inserting into cache from local trakt data: "+repr(traktData['shows'][change['remoteId']]))
                            show = traktData['shows'][change['remoteId']]
                            if show is not None:
                                show.save()
                        else:
                            Debug("[TraktCache] Inserting into cache from remote trakt data")
                            show = Show.download(change['remoteId'])
                            if show is not None:
                                show.save()
    if 'episodes' in changes:
        for change in changes['episodes']:
            Debug("[TraktCache] Cache update: "+repr(change))
            if 'remoteId' in change and 'subject' in change and 'value' in change:
                if change['subject'] in ('title', 'overview', 'firstAired', 'playCount', 'rating', 'watchlistStatus', 'libraryStatus', 'screen'):
                    with SafeShelf('episodes') as episodes:
                        exists = change['remoteId'] in episodes
                        if exists:
                            episode = episodes[change['remoteId']]
                    if exists:
                        episode = episodes[change['remoteId']]
                        
                        Debug("[TraktCache] Updating "+unicode(episode)+", setting "+str(change['subject'])+" to "+unicode(change['value']))
                        episode['_'+change['subject']] = change['value']
                        if 'bestBefore' in change:
                            episode._bestBefore[change['subject']] = change['bestBefore']
                        with SafeShelf('episodes', True) as episodes:
                            episodes[change['remoteId']] = episode
                    else:
                        if 'episodes' in traktData and change['remoteId'] in traktData['episodes']:
                            Debug("[TraktCache] Inserting into cache from local trakt data: "+repr(traktData['episodes'][change['remoteId']]))
                            episode = traktData['episodes'][change['remoteId']]
                            if episode is not None:
                                episode.save()
                        else:
                            Debug("[TraktCache] Inserting into cache a shell episode")
                            episode = Episode(change['remoteId'], static=True)
                            if episode is not None:
                                episode.save()

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
    if 'shows' in changes:
        cacheChanges['shows'] = []
        for change in changes['shows']:
            Debug("[TraktCache] XBMC update: "+repr(change))
            if 'remoteId' in change and 'subject' in change and 'value' in change:
                if change['subject'] in ('title', 'year', 'firstAired', 'country', 'overview', 'runtime', 'network', 'airDay', 'airTime', 'classification', 'rating', 'watchlistStatus', 'recommendedStatus', 'libraryStatus', 'poster', 'fanart', 'episodes'):
                    # ignore, irrelevant, pass on to update the cache
                    pass
                else:
                    # invalid
                    continue
                # succeeded
                cacheChanges['shows'].append(change)
    if 'episodes' in changes:
        cacheChanges['episodes'] = []
        for change in changes['episodes']:
            Debug("[TraktCache] XBMC update: "+repr(change))
            if 'remoteId' in change and 'subject' in change and 'value' in change:
                if change['subject'] == 'playcount':
                    showId, season, episode = Episode.devolveId(change['remoteId'])
                    if setXBMCEpisodePlaycount(showId, season, episode, change['value']) is None:
                        continue # failed, skip
                elif change['subject'] in ('title', 'overview', 'firstAired', 'rating', 'watchlistStatus', 'libraryStatus', 'screen'):
                    # ignore, irrelevant, pass on to update the cache
                    pass
                else:
                    # invalid
                    continue
                # succeeded
                cacheChanges['episodes'].append(change)
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
        if 'shows' in newChanges:
            # Add and new changes to the queue
            for change in newChanges['shows']:
                if change not in changeQueue['shows']: # Check that we arn't adding duplicates
                    changeQueue['shows'].append(change)
            
            with SafeShelf('shows', True) as shows:
                shows['_queue'] = changeQueue['shows']
        if 'episodes' in newChanges:
            # Add and new changes to the queue
            for change in newChanges['episodes']:
                if change not in changeQueue['episodes']: # Check that we arn't adding duplicates
                    changeQueue['episodes'].append(change)
            
            with SafeShelf('episodes', True) as episodes:
                episodes['_queue'] = changeQueue['episodes']
    
    cacheChanges = {}
    
    #Debug("[~] CQ: "+repr(changeQueue))
    if 'movies' in changeQueue:
        for item in changeQueue['movies']:
            Debug("[~] M> "+str(item['subject'])+"\t "+str(item['remoteId'])+"\t "+str(item['value']))
        cacheChanges['movies'] = []
        for change in changeQueue['movies']:
            Debug("[TraktCache] trakt update: "+repr(change))
            if 'remoteId' in change and 'subject' in change and 'value' in change:
                if change['subject'] == 'watchlistStatus':
                    if change['value'] == True:
                        if Trakt.movieWatchlist([Movie(change['remoteId']).traktise()]) is None:
                            continue # failed, leave in queue for next time
                    else:
                        if Trakt.movieUnwatchlist([Movie(change['remoteId']).traktise()]) is None:
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
                    movie = Movie(change['remoteId']).traktise()
                    if Trakt.rateMovie(movie['imdb_id'], movie['title'], movie['year'], change['value'], movie['tmdb_id']) is None:
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
    if 'shows' in changeQueue:
        for item in changeQueue['shows']:
            Debug("[~] S> "+str(item['subject'])+"\t "+str(item['remoteId'])+"\t "+str(item['value']))
        cacheChanges['shows'] = []
        for change in changeQueue['shows']:
            Debug("[TraktCache] trakt update: "+repr(change))
            if 'remoteId' in change and 'subject' in change and 'value' in change:
                if change['subject'] == 'watchlistStatus':
                    if change['value'] == True:
                        if Trakt.showWatchlist([Show(change['remoteId']).traktise()]) is None:
                            continue # failed, leave in queue for next time
                    else:
                        if Trakt.showUnwatchlist([Show(change['remoteId']).traktise()]) is None:
                            continue # failed, leave in queue for next time
                elif change['subject'] == 'rating':
                    show = Show(change['remoteId']).traktise()
                    if Trakt.rateShow(show['tvdb_id'], show['title'], show['year'], change['value'], show['imdb_id']) is None:
                        continue # failed, leave in queue for next time
                elif change['subject'] in ('title', 'year', 'firstAired', 'country', 'overview', 'runtime', 'network', 'airDay', 'airTime', 'classification', 'recommendedStatus', 'poster', 'fanart', 'episodes'):
                    # ignore, irrelevant, pass on to update the cache
                    pass
                else:
                    # invalid
                    with SafeShelf('shows', True) as shows:
                        queue = shows['_queue']
                        queue.remove(change)
                        shows['_queue'] = queue
                    continue
                # succeeded
                cacheChanges['shows'].append(change)
            # either succeeded or invalid
            with SafeShelf('shows', True) as shows:
                queue = shows['_queue']
                queue.remove(change)
                shows['_queue'] = queue
    if 'episodes' in changeQueue:
        for item in changeQueue['episodes']:
            Debug("[~] E> "+str(item['subject'])+"\t "+str(item['remoteId'])+"\t "+str(item['value']))
        cacheChanges['episodes'] = []
        for change in changeQueue['episodes']:
            Debug("[TraktCache] trakt update: "+repr(change))
            if 'remoteId' in change and 'subject' in change and 'value' in change:
                if change['subject'] == 'watchlistStatus':
                    if change['value'] == True:
                        if Trakt.showEpisodeWatchlist([Episode(change['remoteId']).traktise()]) is None:
                            continue # failed, leave in queue for next time
                    else:
                        if Trakt.showEpisodeUnwatchlist([Episode(change['remoteId']).traktise()]) is None:
                            continue # failed, leave in queue for next time
                elif change['subject'] == 'playcount':
                    episode = Episode(change['remoteId']).traktise()
                    if (change['value'] >= 0):
                        if (change['value'] == 0):
                            if Trakt.showEpisodeUnseen(episode['tvdb_id'], episode['title'], episode['year'], [{'season': episode['season'], 'episode': episode['episode']}], episode['imdb_id']) is None:
                                continue # failed, leave in queue for next time
                        else:
                            if Trakt.showEpisodeSeen(episode['tvdb_id'], episode['title'], episode['year'], [{'season': episode['season'], 'episode': episode['episode']}], episode['imdb_id']) is None:
                                continue # failed, leave in queue for next time
                elif change['subject'] == 'libraryStatus':
                    episode = Episode(change['remoteId']).traktise()
                    if change['value'] == True:
                        if Trakt.showEpisodeLibrary(episode['tvdb_id'], episode['title'], episode['year'], [{'season': episode['season'], 'episode': episode['episode']}], episode['imdb_id']) is None:
                            continue # failed, leave in queue for next time
                    else:
                        if Trakt.showEpisodeUnlibrary(episode['tvdb_id'], episode['title'], episode['year'], [{'season': episode['season'], 'episode': episode['episode']}], episode['imdb_id']) is None:
                            continue # failed, leave in queue for next time
                elif change['subject'] == 'rating':
                    episode = Episode(change['remoteId']).traktise()
                    if Trakt.rateEpisode(episode['tvdb_id'], episode['showtitle'], episode['year'], episode['season'], episode['episode'], change['value'], episode['imdb_id']) is None:
                        continue # failed, leave in queue for next time
                elif change['subject'] in ('title', 'overview', 'firstAired', 'screen'):
                    # ignore, irrelevant, pass on to update the cache
                    pass
                else:
                    # invalid
                    with SafeShelf('episodes', True) as episodes:
                        queue = episodes['_queue']
                        queue.remove(change)
                        episodes['_queue'] = queue
                    continue
                # succeeded
                cacheChanges['episodes'].append(change)
            # either succeeded or invalid
            with SafeShelf('episodes', True) as episodes:
                queue = episodes['_queue']
                queue.remove(change)
                episodes['_queue'] = queue
    trakt_cache._updateCache(cacheChanges, traktData)

##
# DB Readers
##

@async
def _copyTraktMovies():
    movies = {}
    traktMovies = AsyncCall(Trakt.userLibraryMoviesAll, None, username, daemon=True)
    watchlistMovies = AsyncCall(Trakt.userWatchlistMovies, None, username)
    
    traktMovies = ~traktMovies
    watchlistMovies = ~watchlistMovies
    if traktMovies is None: return movies
    watchlistMovies = traktMovieListByImdbID(watchlistMovies)
    for movie in traktMovies:
        local = Movie.fromTrakt(movie)
        if local is None:
            continue
        if watchlistMovies is not None and 'imdb_id' in movie:
            local._watchlistStatus = movie['imdb_id'] in watchlistMovies
        movies[local._remoteId] = local
    return movies

@async
def _copyTraktShows():
    shows = {}
    traktShows = Trakt.userLibraryShowsAll(username, daemon=True)
    
    for show in traktShows:
        local = Show.fromTrakt(show)
        if local is None:
            continue
        shows[local._remoteId] = local
    return shows

@async
def _copyTraktEpisodes():
    episodes = {}
    traktShowsCollection = Trakt.userLibraryShowsCollection(username, daemon=True)
    
    for show in traktShowsCollection:
        local = Show.fromTrakt(show)
        if local is None: continue
        remoteId = local._remoteId
        for season in show['seasons']:
            s = season['season']
            for e in season['episodes']:
                episode = Episode(str(remoteId)+'@'+str(s)+'x'+str(e), static=True)
                episode._libraryStatus = True;
                episodes[episode._remoteId] = episode
    return episodes
    
def _copyTrakt():
    traktData = {}
                        
    movies = _copyTraktMovies()
    shows = _copyTraktShows()
    episodes = _copyTraktEpisodes()
        
    traktData['movies'] = ~movies
    traktData['shows'] = ~shows
    traktData['episodes'] = ~episodes
    
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
    xbmcShows = getTVShowsFromXBMC()['tvshows']
    for show in xbmcShows:
        local = Show.fromXbmc(show)
        if local is None:
            continue
        shows[local._remoteId] = local
        
    episodes = {}
    for show in xbmcShows:
        remoteId = Show.fromXbmc(show)._remoteId
        seasons = getSeasonsFromXBMC(show)
        if seasons is not None and 'seasons' in seasons:
            seasons = seasons['seasons']
            for season in seasons:
                s = season['season']
                xbmcEpisodes = getEpisodesFromXBMC(show, s)
                if xbmcEpisodes is not None and 'episodes' in xbmcEpisodes:
                    xbmcEpisodes = xbmcEpisodes['episodes']
                    for episode in xbmcEpisodes:
                        episode = Episode.fromXbmc(remoteId, episode)
                        if episode is not None:
                            episodes[episode._remoteId] = episode
        
    xbmcData['movies'] = movies
    xbmcData['shows'] = shows
    xbmcData['episodes'] = episodes
    return xbmcData

##
# Sync comparitors
##

attributes = {
    'xbmc': {
        'movies': {
            'primary': ['playcount', 'trailer', 'poster', 'fanart'],
            'secondary': ['title', 'year', 'runtime', 'tagline']
        },
        'shows': {
            'primary': ['fanart'],
            'secondary': ['title', 'year']
        },
        'episodes': {
            'primary': ['playcount', 'screen'],
            'secondary': ['title', 'firstAired', 'runtime']
        }
    },
    'trakt': {
        'movies': {
            'primary': ['title', 'year', 'runtime', 'released', 'tagline', 'overview', 'classification', 'playcount', 'rating', 'watchlistStatus', 'recommendedStatus'],
            'secondary': ['trailer', 'poster', 'fanart', 'libraryStatus']
        },
        'shows': {
            'primary': ['rating', 'watchlistStatus', 'recommendedStatus'],
            'secondary': ['poster', 'fanart']
        },
        'episodes': {
            'primary': ['playcount', 'rating', 'watchlistStatus'],
            'secondary': ['screen', 'libraryStatus']
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
        if not validRemoteId(remoteId): continue
        newItem = newer[remoteId]
        if newItem is None: continue
        if newItem['_remoteId'] not in older:
            if xbmc: changes.append({'remoteId': remoteId, 'subject': 'libraryStatus', 'value':True, 'weak': True})
            for attribute in attributes:
                if newItem['_'+attribute] is not None: changes.append({'remoteId': remoteId, 'subject': attribute, 'value':newItem['_'+attribute], 'weak': True, 'bestBefore': time.time()+24*60*60})
            for attribute in weakAttributes:
                if newItem['_'+attribute] is not None: changes.append({'remoteId': remoteId, 'subject': attribute, 'value':newItem['_'+attribute], 'weak': True, 'bestBefore': time.time()+24*60*60})
    
    for remoteId in older:
        if len(remoteId) == 0: continue
        if not validRemoteId(remoteId): continue
        oldItem = older[remoteId]
        if oldItem is None:
            continue
        if remoteId not in newer: #If item not in library
            if xbmc:
                if oldItem['_libraryStatus']: #If item had been in library
                    changes.append({'remoteId': remoteId, 'subject': 'libraryStatus', 'value':False})
        else:
            newItem = newer[remoteId]
            if newItem is None:
                continue
            for attribute in attributes:
                if attribute == 'episodes':
                    if _episodesDifferent(newItem['_'+attribute], oldItem['_'+attribute]): # If the non cached data is different from the old data cached locally
                        if newItem['_'+attribute] is not None: changes.append({'remoteId': remoteId, 'subject': attribute, 'value':newItem['_'+attribute]})
                if newItem['_'+attribute] <> oldItem['_'+attribute]: # If the non cached data is different from the old data cached locally
                    if newItem['_'+attribute] is not None: changes.append({'remoteId': remoteId, 'subject': attribute, 'value':newItem['_'+attribute], 'weak': (oldItem['_'+attribute] is None)})
                oldItem._bestBefore[attribute] = time.time()+24*60*60
            for attribute in weakAttributes:
                if oldItem['_'+attribute] is None: # If the non cached data is different from the old data cached locally
                    if newItem['_'+attribute] is not None: changes.append({'remoteId': remoteId, 'subject': attribute, 'value':newItem['_'+attribute], 'weak': True})
                oldItem._bestBefore[attribute] = time.time()+24*60*60
        oldItem._bestBefore['libraryStatus'] = time.time()+12*60*60
        if writeBack is None:
            older[remoteId] = oldItem
        elif writeBack == False:
            pass
        else:
            writeBack[remoteId] = oldItem
    return changes
    
def _episodesDifferent(newEpisodes, oldEpisodes):
    diff = set(newEpisodes.keys()) - set(oldEpisodes.keys())
    if diff.length <> 0: return True
    for season in newEpisodes:
        diff = set(newEpisodes[season].keys()) - set(oldEpisodes[season].keys())
        if diff.length <> 0: return True
    return False
    
def makeChanges(changes, traktOnly = False, xbmcOnly = False):
    Debug("[~] Made changes: "+repr(changes))
    if not traktOnly: _updateXbmc(changes)
    if not xbmcOnly: _updateTrakt(changes)

##
# Sync timing
##

def trigger():
    Debug("[TraktCache] Starting triggered updates")
    Debug("[TraktCache] Getting partial list of changes")
    if not getActivityUpdates(): # if the activity updates might ve missing some data
        Debug("[TraktCache] Getting extended list of changes")
        needSyncAtLeast(['library', 'watchlist'], force=True)
    Debug("[TraktCache] Updating stale sets")
    needSyncAtLeast(['all'])
    Debug("[TraktCache] All triggered updates complete")

_setStucture = {
    'all': {
        'movieall': {
            'movielibrary': {},
            'movierecommended': {},
            'moviewatchlist': {},
        },
        'showall': {
            'showrecommended': {},
            'showwatchlist': {},
        },
        'episodeall': {
            'episodelibrary': {},
            'episodewatchlist': {},
        },
        'library': {
            'movielibrary': {},
            'episodelibrary': {},
        },
        'movielibrary': {
            'movieseen': {},
        },
        'episodelibrary': {
            'episodeseen': {},
        },
        'watchlist': {
           'moviewatchlist': {},
           'showwatchlist': {},
           'episodewatchlist': {},
        },
    }
}
    
syncTimes = {'episodelibrary': 6*60*60,
             'episodeseen': 3*60*60,
             'episodewatchlist': 10*60,
             'episodeimages': 12*60*60,
             'episodeall': 24*60*60,
             'showrecommended': 60*60,
             'showwatchlist': 10*60,
             'showimages': 12*60*60,
             'showall': 24*60*60,
             'moviewatchlist': 10*60,
             'movierecommended': 60*60,
             'movieseen': 3*60*60,
             'movielibrary': 6*60*60,
             'movieimages': 12*60*60,
             'movieall': 24*60*60,
             'library': 60*60,
             'watchlist': 30*60,
             'all': 24*60*60,
             'useractivity': 2*60*60,
             'friendsactivity': 3*60*60}

def getActivityUpdates(force=False):
    checkUserActivity = -1
    userActCount = 0
    checkFriendsActivity = -1
    friendsActCount = 0
    with SafeShelf('expire') as expire:
        if 'useractivity' not in expire or expire['useractivity'] is None:
            expire['useractivity'] = time.time()
        if expire['useractivity'] < time.time()-syncTimes['useractivity'] or force:
            checkUserActivity = expire['useractivity']
        if 'friendsactivity' not in expire or expire['friendsactivity'] is None:
            expire['friendsactivity'] = time.time()
        if expire['friendsactivity'] < time.time()-syncTimes['friendsactivity'] or force:
            checkFriendsActivity = expire['friendsactivity']
    if checkUserActivity <> -1:
        timeStamp, userActCount = refreshFromUserActivity(checkUserActivity)
        with SafeShelf('expire', True) as expire:
            expire['useractivity'] = timeStamp
    """if checkFriendsActivity <> -1:
        timeStamp, friendsActCount = refreshFromFriendsActivity(checkFriendsActivity)
        with SafeShelf('expire', True) as expire:
            expire['friendsactivity'] = timeStamp"""
    if userActCount >= 100 or friendsActCount >= 100:
        return False
    return True
    
def updateSyncTimes(sets = [], remoteIds = []):
    updated = {}
    sets = set(sets)
    sets, _ = setPropergatePositive(sets, _setStucture)
    
    with SafeShelf('expire', True) as expire:
        for updatedSet in sets:
            if updatedSet not in syncTimes:
                Debug("[TraktCache] Tried to bump update time of unknown update set:" +updatedSet)
                continue
            Debug("[TraktCache] Updating timestamp for "+str(updatedSet))
            expire[updatedSet] = time.time() + syncTimes[updatedSet]
        for remoteId in remoteIds:
            expire[remoteId] = time.time() + 10*60 # +10mins

def setPropergatePositive(sets, structure):
    more = True
    found = False
    done = set([])
    checked = set([])
    while more:
        more = False
        for item in structure:
            if item in sets and item not in done:
                sets |= set(structure[item].keys())
                done.add(item)
                checked.discard(item)
                found = True
                more = True
            subFound = False
            if item not in checked:
                sets, subFound = setPropergatePositive(sets, structure[item])
                checked.add(item)
            if subFound:
                more = True
                found = True
    return sets, found

def needSyncAtLeast(sets = [], movieIds = [], showIds = [], episodeIds = [], force = False):
    # This function should block untill all syncs have been satisfied
    sets = set(sets)
    sets = setPropergateNegative(sets, _setStucture)
    for staleSet in sets:
        with SafeShelf('expire') as expire:
            stale = staleSet not in expire or expire[staleSet] < time.time() or force
        if stale:
            refreshSet(staleSet)
    for remoteId in movieIds:
        with SafeShelf('expire') as expire:
            stale = remoteId not in expire or expire[remoteId] < time.time() or force
        if stale:
            refreshMovie(remoteId)
    for remoteId in showIds:
        with SafeShelf('expire') as expire:
            stale = remoteId not in expire or expire[remoteId] < time.time() or force
        if stale:
            refreshShow(remoteId)
    for remoteId in episodeIds:
        with SafeShelf('expire') as expire:
            stale = remoteId not in expire or expire[remoteId] < time.time() or force
        if stale:
            refreshEpisode(remoteId)
    return

def setPropergateNegative(sets, structure, fireSale=False):
    for item in structure:
        if fireSale or item in sets:
            sets -= set(structure[item].keys())
            sets = setPropergateNegative(sets, structure[item], fireSale=True)
        else:
            sets = setPropergateNegative(sets, structure[item])
    return sets

##
# Items
##

def getMovie(remoteId = None, localId = None):
    if remoteId is None and localId is None:
        raise ValueError("Must provide at least one form of id")
    if remoteId is None:
        remoteId = trakt_cache.getMovieRemoteId(localId)
    if remoteId is None:
        return None
    with SafeShelf('movies') as movies:
        if remoteId not in movies:
            return None
        return movies[remoteId]

def getShow(remoteId = None, localId = None):
    if remoteId is None and localId is None:
        raise ValueError("Must provide at least one form of id")
    if remoteId is None:
        remoteId = trakt_cache.getShowRemoteId(localId)
    if remoteId is None:
        return None
    with SafeShelf('shows') as shows:
        if remoteId not in shows:
            return None
        return shows[remoteId]
        
def getEpisode(remoteId = None, localId = None):
    if remoteId is None and localId is None:
        raise ValueError("Must provide at least one form of id")
    if remoteId is None:
        remoteId = trakt_cache.getEpisodeRemoteId(localId)
    if remoteId is None:
        return None
    with SafeShelf('episodes') as episodes:
        if remoteId not in episodes:
            return None
        return episodes[remoteId]
        
def getMovieRemoteId(localId):
    with SafeShelf('movies') as movies:
        if '_byLocalId' in movies and localId in movies['_byLocalId']:
            return movies['_byLocalId'][localId]
    return None     
    
def getShowRemoteId(localId):
    with SafeShelf('shows') as shows:
        if '_byLocalId' in shows and localId in shows['_byLocalId']:
            return shows['_byLocalId'][localId]
    return None
            
def getEpisodeRemoteId(localId):
    with SafeShelf('episodes') as episodes:
        if '_byLocalId' in episodes and localId in episodes['_byLocalId']:
            return episodes['_byLocalId'][localId]
    return None

def getMovieLocalIds(remoteId):
    hits = []
    with SafeShelf('movies') as movies:
        for localId in movies['_byLocalId']:
            if remoteId == movies['_byLocalId'][localId]:
                hits.append(localId)
    return hits
    
def getShowLocalIds(remoteId):
    hits = []
    with SafeShelf('shows') as shows:
        for localId in shows['_byLocalId']:
            if remoteId == shows['_byLocalId'][localId]:
                hits.append(localId)
    return hits
    
def getEpisodeLocalIds(remoteId):
    hits = []
    with SafeShelf('episodes') as episodes:
        for localId in episodes['_byLocalId']:
            if remoteId == episodes['_byLocalId'][localId]:
                hits.append(localId)
    return hits

def relateMovieId(localId, remoteId):
    with SafeShelf('movies', True) as movies:
        if '_byLocalId' in movies:
            index = movies['_byLocalId']
        else:
            index = {}
        index[localId] = remoteId
        movies['_byLocalId'] = index
        
def relateShowId(localId, remoteId):
    with SafeShelf('shows', True) as shows:
        if '_byLocalId' in shows:
            index = shows['_byLocalId']
        else:
            index = {}
        index[localId] = remoteId
        shows['_byLocalId'] = index
        
def relateEpisodeId(localId, remoteId):
    with SafeShelf('episodes', True) as episodes:
        if '_byLocalId' in episodes:
            index = episodes['_byLocalId']
        else:
            index = {}
        index[localId] = remoteId
        episodes['_byLocalId'] = index
      
def refreshMovie(remoteId, property = None):
    localIds = getMovieLocalIds(remoteId)
    if len(localIds) == 0:
        localId = None
    else:
        localId  = localIds[0]
    xbmcData = None
    cacheData = None
    if localId is not None:
        movie = Movie.fromXbmc(getMovieDetailsFromXbmc(localId,['title', 'year', 'originaltitle', 'imdbnumber', 'playcount', 'lastplayed', 'runtime']))
        if movie is not None:
            xbmcData = {'movies': {remoteId: movie}}
        else:
            xbmcData = {'movies': {}}
    if property is not None:
        if property in ('title', 'year', 'runtime', 'released', 'tagline', 'overview', 'classification', 'playcount', 'rating', 'watchlistStatus', 'libraryStatus', 'traktDbStatus', 'trailer', 'poster', 'fanart'):
            movie = Movie.download(remoteId)
            if movie is not None:
                traktData = {'movies': {remoteId: movie}}
            else:
                traktData = {'movies': {}}
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
        
def saveShow(show):
    with SafeShelf('shows', True) as shows:
        shows[show.remoteId] = show
        
def saveEpisode(episode):
    with SafeShelf('episodes', True) as episodes:
        episodes[episode.remoteId] = episode

def newLocalMovie(localId):
    movie = Movie.fromXbmc(getMovieDetailsFromXbmc(localId,['title', 'year', 'originaltitle', 'imdbnumber', 'playcount', 'lastplayed', 'runtime']))
    movie.save()
    relateMovieId(localId, movie.remoteId)
    movie.refresh()
  
    
##
# Activity Updates
##

def refreshFromUserActivity(lastTimestamp):
    responce = Trakt.activityUsers(username, timestamp=lastTimestamp)
    changes = {}
    changes['episodes'] = []
    changes['movies'] = []
    changes['shows'] = []
    for event in responce['activity']:
        Debug("Update activity, "+str(event['type'])+'/'+str(event['action']))
        if event['type'] == 'episode':
            if event['action'] == 'watching':
                continue #ignore
            if event['action'] == 'scrobble':
                episode = Episode.fromTrakt(event['show'], event['episode'])
                changes['episodes'].append({'remoteId': episode.remoteId, 'subject': 'playcount', 'value':episode._playcount, 'bestBefore': time.time()+6*60*60})
            if event['action'] == 'checkin':
                continue #ignore
            if event['action'] == 'seen':
                for traktEpisode in event['episodes']:
                    episode = Episode.fromTrakt(event['show'], event['episode'])
                changes['episodes'].append({'remoteId': episode.remoteId, 'subject': 'playcount', 'value':episode._playcount, 'bestBefore': time.time()+6*60*60})
            if event['action'] == 'collection':
                for traktEpisode in event['episodes']:
                    episode = Episode.fromTrakt(event['show'], traktEpisode)
                    changes['episodes'].append({'remoteId': episode.remoteId, 'subject': 'libraryStatus', 'value':episode._libraryStatus, 'bestBefore': time.time()+6*60*60})
            if event['action'] == 'rating':
                episode = Episode.fromTrakt(event['show'], event['episode'])
                changes['episodes'].append({'remoteId': episode.remoteId, 'subject': 'rating', 'value':episode._rating, 'bestBefore': time.time()+6*60*60})
            if event['action'] == 'watchlist':
                episode = Episode.fromTrakt(event['show'], event['episode'])
                changes['episodes'].append({'remoteId': episode.remoteId, 'subject': 'watchlistStatus', 'value':episode._watchlistStatus, 'bestBefore': time.time()+6*60*60})
            if event['action'] == 'shout':
                continue #ignore
        if event['type'] == 'show':
            if event['action'] == 'rating':
                show = Show.fromTrakt(event['show'])
                changes['shows'].append({'remoteId': show.remoteId, 'subject': 'rating', 'value':show._rating, 'bestBefore': time.time()+6*60*60})
            if event['action'] == 'watchlist':
                show = Show.fromTrakt(event['show'])
                changes['shows'].append({'remoteId': show.remoteId, 'subject': 'watchlistStatus', 'value':show._watchlistStatus, 'bestBefore': time.time()+6*60*60})
            if event['action'] == 'shout':
                continue #ignore
        if event['type'] == 'movie':
            if event['action'] == 'watching':
                continue #ignore
            if event['action'] == 'scrobble':
                movie = Movie.fromTrakt(event['movie'])
                changes['movies'].append({'remoteId': movie.remoteId, 'subject': 'playcount', 'value':movie._playcount, 'bestBefore': time.time()+6*60*60})
            if event['action'] == 'checkin':
                continue #ignore
            if event['action'] == 'seen':
                movie = Movie.fromTrakt(event['movie'])
                changes['movies'].append({'remoteId': movie.remoteId, 'subject': 'playcount', 'value':movie._playcount, 'bestBefore': time.time()+6*60*60})
            if event['action'] == 'collection':
                movie = Movie.fromTrakt(event['movie'])
                changes['movies'].append({'remoteId': movie.remoteId, 'subject': 'libraryStatus', 'value':movie._libraryStatus, 'bestBefore': time.time()+6*60*60})
            if event['action'] == 'rating':
                movie = Movie.fromTrakt(event['movie'])
                changes['movies'].append({'remoteId': movie.remoteId, 'subject': 'rating', 'value':movie._rating, 'bestBefore': time.time()+6*60*60})
            if event['action'] == 'watchlist':
                movie = Movie.fromTrakt(event['movie'])
                changes['movies'].append({'remoteId': movie.remoteId, 'subject': 'watchlistStatus', 'value':movie._watchlistStatus, 'bestBefore': time.time()+6*60*60})
            if event['action'] == 'shout':
                continue #ignore
    
    trakt_cache._updateXbmc(changes) 
    return responce['timestamps']['current'], len(responce['activity'])
    
def refreshFromFriendsActivity(lastTimestamp):
    raise NotImplementedError("This function has not been written")
    
"""def compareNewer(xbmcData=None, traktData=None):
    if xbmcData is None and traktData is None:
        return
    cacheData = {}
    cacheData['movies'] = []
    for movie in xbmcData['movies']:
        item = getMovie(movie._remoteId)
        if item is not None:
            cacheData['movies'].append(item)
    cacheData['shows'] = []
    for show in xbmcData['shows']:
        item = getShow(show._remoteId)
        if item is not None:
            cacheData['shows'].append(item)
    cacheData['episodes'] = []
    for episode in xbmcData['episodes']:
        item = getEpisode(episode._remoteId)
        if item is not None:
            cacheData['episodes'].append(item)
    if xbmcData is None:
        xbmcData = {}
        xbmcData['movies'] = []
        for movie in xbmcData['movies']:
            localIds = getMovieLocalIds(remoteId)
            if len(localIds) > 0:
                item = Movie.fromXbmc(getMovieDetailsFromXbmc(localIds[0],['title', 'year', 'originaltitle', 'imdbnumber', 'playcount', 'lastplayed', 'runtime']))
                if item is not None:
                    xbmcData['movies'].append(item)
        if item is not None:
            cacheData['movies'].append(item)
        
    if traktData is None:
        
    _sync(xbmcData, traktData, cacheData)"""
        
        

##
# Sets
##
   
def getMovieLibrary():
    needSyncAtLeast(['movielibrary'])
    items = []
    with SafeShelf('movies') as movies:
        for remoteId in movies:
            if not validRemoteId(remoteId): continue
            movie = movies[remoteId]
            if movie is None:
                continue
            items.append(movie)
    return items
def getShows():
    raise NotImplementedError()
def getShowEpisodes():
    raise NotImplementedError()
def getMovieWatchList():
    needSyncAtLeast(['moviewatchlist'])
    watchlist = []
    with SafeShelf('movies') as movies:
        for remoteId in movies:
            if not validRemoteId(remoteId): continue
            movie = movies[remoteId]
            if movie is None:
                continue
            if movie['_watchlistStatus'] == True:
                watchlist.append(movie)
    return watchlist    
def getRecommendedMovies():
    needSyncAtLeast(['movierecommended'])
    items = []
    with SafeShelf('movies') as movies:
        for remoteId in movies:
            if not validRemoteId(remoteId): continue
            movie = movies[remoteId]
            if movie is None:
                continue
            if movie['_recommendedStatus'] == True:
                items.append(movie)
    return items
def getTrendingMovies():
    traktItems = Trakt.moviesTrending();
    items = []
    for movie in traktItems:
        localMovie = Movie.fromTrakt(movie)
        items.append(localMovie)
    return items

def refreshSet(set, _structure=None):
    if set in _refresh and _refresh[set] is not None:
        _refresh[set]()
        return True
    else:
        if _structure is None:
            _structure = _setStucture
        if set in _structure:
            complete = False
            for subSet in _structure[set]:
                if refreshSet(subSet, _structure=_structure[set]):
                    complete = True
            if complete:
                updateSyncTimes([set])
            return complete
        else:
            for subSet in _structure:
                refreshSet(set, _structure=_structure[subSet])
            if len(_structure.keys())==0:
                Debug("[TraktCache] No method specified to refresh the set: "+str(set))
    return False

def refreshLibrary():
    Debug("[TraktCache] Refreshing library")
    # Send changes to trakt
    trakt_cache._updateTrakt()
    
    # Receive latest according to trakt
    traktData = trakt_cache._copyTrakt()
    # Get latest xbmc
    xbmcData = trakt_cache._copyXbmc()
    
    _sync(xbmcData, traktData)  
    updateSyncTimes(['library'])
    
def refreshMovieWatchlist():
    Debug("[TraktCache] Refreshing movie watchlist")
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
            if not validRemoteId(remoteId): continue
            movie = movies[remoteId]
            if movie is None:
                continue
            if movie['_watchlistStatus'] <> (remoteId in watchlist):
                movie['_watchlistStatus'] = not movie['_watchlistStatus']
                movies[movie['_remoteId']] = movie
    updateSyncTimes(['moviewatchlist'], watchlist.keys())
    
def refreshShowWatchlist():
    Debug("[TraktCache] Refreshing show watchlist")
    traktWatchlist = Trakt.userWatchlistShows(username)
    watchlist = {}
    traktData = {}
    traktData['shows'] = []
    for show in traktWatchlist:
        localShow = Show.fromTrakt(show)
        watchlist[localShow['_remoteId']] = localShow
    traktData['shows'] = watchlist
    _sync(traktData = traktData)
    with SafeShelf('shows', True) as shows:
        for remoteId in shows:
            if not validRemoteId(remoteId): continue
            show = shows[remoteId]
            if show is None:
                continue
            if show['_watchlistStatus'] <> (remoteId in watchlist):
                show['_watchlistStatus'] = not show['_watchlistStatus']
                shows[show['_remoteId']] = show
    updateSyncTimes(['showwatchlist'], watchlist.keys())
        
def refreshEpisodeWatchlist():
    Debug("[TraktCache] Refreshing episode watchlist")
    traktWatchlist = Trakt.userWatchlistEpisodes(username)
    watchlist = {}
    traktData = {}
    traktData['episodes'] = []
    for episode in traktWatchlist:
        localEpisode = Episode.fromTrakt(show)
        watchlist[localEpisode['_remoteId']] = localEpisode
    traktData['episodes'] = watchlist
    _sync(traktData = traktData)
    with SafeShelf('episodes', True) as episodes:
        for remoteId in episodes:
            if not validRemoteId(remoteId): continue
            episode = episodes[remoteId]
            if episode is None:
                continue
            if episode['_watchlistStatus'] <> (remoteId in watchlist):
                episode['_watchlistStatus'] = not episode['_watchlistStatus']
                episodes[episode['_remoteId']] = episode
    updateSyncTimes(['episodewatchlist'], watchlist.keys())
    
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
            if not validRemoteId(remoteId): continue
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
    
def refreshRecommendedShows():
    Debug("[TraktCache] Refreshing recommended shows")
    traktItems = Trakt.recommendationsShows()
    items = {}
    traktData = {}
    traktData['shows'] = []
    for show in traktItems:
        localShow = Show.fromTrakt(show)
        items[localShow['_remoteId']] = localShow
    traktData['shows'] = items
    _sync(traktData = traktData)
    with SafeShelf('shows', True) as shows:
        for remoteId in shows:
            if not validRemoteId(remoteId): continue
            show = shows[remoteId]
            if show is None:
                continue
            status = remoteId in items;
            if show['_recommendedStatus'] <> True and status:
                show['_recommendedStatus'] = True
                shows[show['_remoteId']] = show
            elif show['_recommendedStatus'] <> False and not status:
                show['_recommendedStatus'] = False
                shows[show['_remoteId']] = show
            
    updateSyncTimes(['showrecommended'], items.keys())
    
_refresh = {}
_refresh['all'] = None
_refresh['library'] = refreshLibrary
_refresh['movieall'] = None
_refresh['movielibrary'] = None
_refresh['episodelibrary'] = None
_refresh['moviewatchlist'] = refreshMovieWatchlist
_refresh['movierecommended'] = refreshRecommendedMovies
_refresh['movieseen'] = None
_refresh['showall'] = None
_refresh['showrecommended'] = refreshRecommendedShows
_refresh['showwatchlist'] = refreshShowWatchlist
_refresh['episodeall'] = None
_refresh['episodelibrary'] = None
_refresh['episodewatchlist'] = refreshEpisodeWatchlist
_refresh['episodeseen'] = None
