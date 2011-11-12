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
class Movie(object):
    
    def __init__(self, remoteId, static=False):
        if remoteId is None:
            raise ValueError("Must provide the id for the movie")
        self._remoteId = str(remoteId)
        self._title = None
        self._year = None
        self._runtime = None
        self._released = None
        self._tagline = None
        self._overview = None
        self._classification = None
        self._playcount = None
        self._rating = None
        self._watchlistStatus = None
        self._recommendedStatus = None
        self._libraryStatus = None
        self._traktDbStatus = None
        
        self._trailer = None
        
        self._poster = None
        self._fanart = None
        
        self._bestBefore = {}
        self._static = static
        
    def __repr__(self):
        return "<"+repr(self._title)+" ("+str(self._year)+") - "+str(self._remoteId)+","+str(self._libraryStatus)+","+str(self._poster)+","+str(self._runtime)+","+str(self._tagline)+">"
        
    def __str__(self):
        return unicode(self._title)+" ("+str(self._year)+")"
    
    def __getitem__(self, index):
        if index == "_remoteId": return self._remoteId
        if index == "_title": return self._title
        if index == "_year": return self._year
        if index == "_runtime": return self._runtime
        if index == "_released": return self._released
        if index == "_tagline": return self._tagline
        if index == "_overview": return self._overview
        if index == "_classification": return self._classification
        if index == "_playcount": return self._playcount
        if index == "_rating": return self._rating
        if index == "_watchlistStatus": return self._watchlistStatus
        if index == "_recommendedStatus": return self._recommendedStatus
        if index == "_libraryStatus": return self._libraryStatus
        if index == "_trailer": return self._trailer
        if index == "_poster": return self._poster
        if index == "_fanart": return self._fanart
    
    def __setitem__(self, index, value):
        if index == "_remoteId": self._remoteId = value
        if index == "_title": self._title = value
        if index == "_year": self._year = value
        if index == "_runtime": self._runtime = value
        if index == "_released": self._released = value
        if index == "_tagline": self._tagline = value
        if index == "_overview": self._overview = value
        if index == "_classification": self._classification = value
        if index == "_playcount": self._playcount = value
        if index == "_rating": self._rating = value
        if index == "_watchlistStatus": self._watchlistStatus = value
        if index == "_recommendedStatus": self._recommendedStatus = value
        if index == "_libraryStatus": self._libraryStatus = value
        if index == "_trailer": self._trailer = value
        if index == "_poster": self._poster = value
        if index == "_fanart": self._fanart = value
    
    
    def save(self):
        self._static = False
        trakt_cache.saveMovie(self)
        
    def refresh(self, property = None):
        if not self._static:
            trakt_cache.refreshMovie(self._remoteId, property)
            newer = trakt_cache.getMovie(remoteId)
            
            self._title = newer._title
            self._year = newer._year
            self._runtime = newer._runtime
            self._released = newer._released
            self._tagline = newer._tagline
            self._overview = newer._overview
            self._classification = newer._classification
            self._playcount = newer._playcount
            self._rating = newer._rating
            self._watchlistStatus = newer._watchlistStatus
            self._recommendedStatus = newer._recommendedStatus
            self._libraryStatus = newer._libraryStatus
            self._traktDbStatus = newer._traktDbStatus
            
            self._trailer = newer._trailer
            
            self._poster = newer._poster
            self._fanart = newer._fanart
            
            self._bestBefore = newer._bestBefore
            self._static = newer._static
        
    @property
    def remoteId(self):
        """A unique identifier for the movie."""
        return self._remoteId
        
    @property
    def title(self):
        """The title of the movie."""
        self.checkExpire('title')
        return self._title
        
    @property
    def year(self):
        """The year the movie was released."""
        self.checkExpire('year')
        return self._year
        
    @property
    def runtime(self):
        """The number of minutes the movie runs for."""
        self.checkExpire('runtime')
        return self._runtime
        
    @property
    def released(self):
        """The date the movie was released."""
        self.checkExpire('released')
        return self._released
        
    @property
    def tagline(self):
        """A tag-line about the movie (like a catch phrase)."""
        self.checkExpire('tagline')
        return self._tagline
        
    @property
    def overview(self):
        """An overview of the movie (like a plot)."""
        self.checkExpire('overview')
        return self._overview
        
    @property
    def classification(self):
        """The content classification indicating the suitible audience."""
        self.checkExpire('classification')
        return self._classification
        
    @property
    def trailer(self):
        """The movies trailer."""
        self.checkExpire('trailer')
        return self._trailer
        
    @property
    def poster(self):
        """The movies poster image."""
        self.checkExpire('poster')
        return self._poster
        
    @property
    def fanart(self):
        """The movies fanart image."""
        self.checkExpire('fanart')
        return self._fanart
        
    def scrobble(self, progress):
        scrobbleMovieOnTrakt(self.traktise(), progress)
    def shout(self, text):
        raise NotImplementedError("This function has not been written")
    def watching(self, progress):
        watchingMovieOnTrakt(self.traktise(), progress)
    @staticmethod
    def cancelWatching():
        cancelWatchingMovieOnTrakt()
    def play(self):
        playMovieById(options = trakt_cache.getMovieLocalIds(self.remoteId))
    
    def Property(func):
        return property(**func()) 
    
    @property
    def rating(self):
        if not self._static: trakt_cache.needSyncAtLeast(remoteIds = [self._remoteId])
        return self._rating
    @rating.setter
    def rating(self, value):
        trakt_cache.makeChanges({'movies': [{'remoteId': self.remoteId, 'subject': 'rating', 'value': value}]}, traktOnly = True)
        
    @property
    def playcount(self):
        """How many time the user has watched the movie."""
        trakt_cache.needSyncAtLeast(remoteIds = [self._remoteId])
        return self._playcount
    @playcount.setter
    def playcount(self, value):
        raise NotImplementedError("This function has not been written")
        
    @property
    def libraryStatus(self):
        """Whether the movie is in the users library."""
        if not self._static: trakt_cache.needSyncAtLeast(['movielibrary'])
        return self._libraryStatus
        
    @property
    def watchingStatus(self):
        """Whether the user is currently watching the movie."""
        raise NotImplementedError("This function has not been written")
        
    @property
    def watchlistStatus(self):
        """Whether the movie is in the users watchlist."""
        if not self._static: trakt_cache.needSyncAtLeast(['moviewatchlist'])
        return self._watchlistStatus
    @watchlistStatus.setter
    def watchlistStatus(self, value):
        raise NotImplementedError("This function has not been written")
        
    @property
    def recommendedStatus(self):
        """Whether the movie is recommended to the user by trakt."""
        if not self._static: trakt_cache.needSyncAtLeast(['movierecommended'])
        returnself._recommendedStatus
    
    def checkExpire(self, property):
        if self._static:
            return
        if property not in self._bestBefore or self._bestBefore[property] < time.time():
            self.refresh(property)
        
    @staticmethod
    def download(remoteId):
        Debug("[Movie] Downloading info for "+str(Movie.devolveId(remoteId)))
        local = Trakt.movieSummary(Movie.devolveId(remoteId))
        if local is None:
            movie = Movie(remoteId, static = True)
            movie._traktDbStatus = False
            return movie
        return Movie.fromTrakt(local, static = True)
    
    def traktise(self):
        movie = {}
        movie['title'] = self._title
        movie['year'] = self._year
        movie['plays'] = self._playcount
        movie['in_watchlist'] = self._watchlistStatus
        movie['in_collection'] = self._libraryStatus
        movie['runtime'] = self._runtime
        
        movie['imdb_id'] = None
        movie['tmdb_id'] = None
        if str(self._remoteId).find('imdb=') == 0:
            movie['imdb_id'] = self._remoteId[5:]
        if str(self._remoteId).find('tmdb=') == 0:
            movie['tmdb_id'] = self._remoteId[5:]
        return movie
        
    @staticmethod
    def fromTrakt(movie, static = False):
        if 'imdb_id' in movie:
            local = Movie("imdb="+movie['imdb_id'], static)
        elif 'tmdb_id' in movie:
            local = Movie("tmdb="+movie['tmdb_id'], static)
        else:
            return None
        local._title = movie['title']
        local._year = movie['year']
        if 'plays' in movie:
            local._playcount = movie['plays']
        if 'in_watchlist' in movie:
            local._watchlistStatus = movie['in_watchlist']
        if 'in_collection' in movie:
            local._libraryStatus = movie['in_collection']
        if 'images' in movie and 'poster' in movie['images']:
            local._poster = movie['images']['poster']
        if 'images' in movie and 'fanart' in movie['images']:
            local._fanart = movie['images']['fanart']
        if 'runtime' in movie:
            local._runtime = movie['runtime']
        if 'released' in movie:
            local._released = movie['released']
        if 'tagline' in movie:
            local._tagline = movie['tagline']
        if 'overview' in movie:
            local._overview = movie['overview']
        if 'certification' in movie:
            local._classification = movie['certification']
        if 'trailer' in movie:
            local._trailer = movie['trailer']
            
        return local
     
    @staticmethod
    def fromXbmc(movie):
        #Debug("[Movie] Creating from: "+str(movie))
        if 'imdbnumber' not in movie or movie['imdbnumber'].strip() == "":
            remoteId = trakt_cache.getMovieRemoteId(movie['movieid'])
            if remoteId is not None:
                local = Movie(remoteId)
            else:
                imdb_id = searchGoogleForImdbId(unicode(movie['title'])+"+"+unicode(movie['year']))
                if imdb_id is None or imdb_id == "":
                    traktMovie = searchTraktForMovie(movie['title'], movie['year'])
                    if traktMovie is None:
                         Debug("[Movie] Unable to find movie '"+unicode(movie['title'])+"' ["+unicode(movie['year'])+"]")
                    else:
                        if 'imdb_id' in traktMovie and traktMovie['imdb_id'] <> "":
                            local = Movie("imdb="+traktMovie['imdb_id'])
                        elif 'tmdb_id' in traktMovie and traktMovie['tmdb_id'] <> "":
                            local = Movie("tmdb="+traktMovie['tmdb_id'])
                        else:
                            return None
                    return None
                else:
                    local = Movie("imdb="+imdb_id)
        else:
            local = Movie(Movie.evolveId(movie['imdbnumber']))
        trakt_cache.relateMovieId(movie['movieid'], local._remoteId)
        if local._remoteId == 'imdb=' or local._remoteId == 'tmdb=':
            Debug("[Movie] Fail tried to use blank remote id for "+repr(movie))
            return None
        local._title = movie['title']
        local._year = movie['year']
        local._playcount = movie['playcount']
        local._runtime = movie['runtime']
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
        