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
class User(object):
    
    def __init__(self, username):
        if remoteId is None:
            raise ValueError("Must provide the id for the movie")
        self._username = str(username)
        self._protected = None
        self._fullName = None
        self._gender = None
        self._age = None
        self._location = None
        self._about = None
        self._joined = None
        self._avatar = None
        self._url = None
        self._approved = None
        
        # Stats
        self._numFriends = None
        self._showsTotalCount = None
        self._showsWatchedCount = None
        self._showsLibraryCount = None
        self._showsShoutsCount = None
        self._showsLovedCount = None
        self._episodesWatchedCount = None
        self._episodesWatchedUniqueCount = None
        self._episodesWatchedTraktCount = None
        self._episodesWatchedTraktUniqueCount = None
        self._episodesWatchedElsewhereCount = None
        self._episodesUnwatchedCount = None
        self._episodesLibraryCount = None
        self._episodesShoutsCount = None
        self._episodesLovedCount = None
        self._moviesWatchedCount = None
        self._moviesWatchedUniqueCount = None
        self._moviesWatchedTraktCount = None
        self._moviesWatchedTraktUniqueCount = None
        self._moviesWatchedElsewhereCount = None
        self._moviesTotalCount = None
        self._moviesUnwatchedCount = None
        self._moviesLibraryCount = None
        self._moviesShoutsCount = None
        self._moviesLovedCount = None
        
    def __repr__(self):
        return "<"+repr(self._fullName)+" ("+str(self._username)+") - "+str(self._age)+","+str(self._gender)
        
    def __str__(self):
        return unicode(self._fullName)+" ("+str(self._username)+")"
    
    def __getitem__(self, index):
        if index == "_username": return self._username
        if index == "_protected": return self._protected
        if index == "_fullName": return self._fullName
        if index == "_gender": return self._gender
        if index == "_age": return self._age
        if index == "_location": return self._location
        if index == "_about": return self._about
        if index == "_joined": return self._joined
        if index == "_avatar": return self._avatar
        if index == "_url": return self._url
        if index == "_approved": return self._approved
        if index == "_numFriends": return self._numFriends
        if index == "_showsTotalCount": return self._showsTotalCount
        if index == "_showsWatchedCount": return self._showsWatchedCount
        if index == "_showsLibraryCount": return self._showsLibraryCount
        if index == "_showsShoutsCount": return self._showsShoutsCount
        if index == "_showsLovedCount": return self._showsLovedCount
        if index == "_episodesWatchedCount": return self._episodesWatchedCount
        if index == "_episodesWatchedUniqueCount": return self._episodesWatchedUniqueCount
        if index == "_episodesWatchedTraktCount": return self._episodesWatchedTraktCount
        if index == "_episodesWatchedTraktUniqueCount": return self._episodesWatchedTraktUniqueCount
        if index == "_episodesWatchedElsewhereCount": return self._episodesWatchedElsewhereCount
        if index == "_episodesUnwatchedCount": return self._episodesUnwatchedCount
        if index == "_episodesLibraryCount": return self._episodesLibraryCount
        if index == "_episodesShoutsCount": return self._episodesShoutsCount
        if index == "_episodesLovedCount": return self._episodesLovedCount
        if index == "_moviesWatchedCount": return self._moviesWatchedCount
        if index == "_moviesWatchedUniqueCount": return self._moviesWatchedUniqueCount
        if index == "_moviesWatchedTraktCount": return self._moviesWatchedTraktCount
        if index == "_moviesWatchedTraktUniqueCount": return self._moviesWatchedTraktUniqueCount
        if index == "_moviesWatchedElsewhereCount": return self._moviesWatchedElsewhereCount
        if index == "_moviesTotalCount": return self._moviesTotalCount
        if index == "_moviesUnwatchedCount": return self._moviesUnwatchedCount
        if index == "_moviesLibraryCount": return self._moviesLibraryCount
        if index == "_moviesShoutsCount": return self._moviesShoutsCount
        if index == "_moviesLovedCount": return self._moviesLovedCount
    
    def __setitem__(self, index, value):
        if index == "_username": self._username = value
        if index == "_protected": self._protected = value
        if index == "_fullName": self._fullName = value
        if index == "_gender": self._gender = value
        if index == "_age": self._age = value
        if index == "_location": self._location = value
        if index == "_about": self._about = value
        if index == "_joined": self._joined = value
        if index == "_avatar": self._avatar = value
        if index == "_url": self._url = value
        if index == "_approved": self._approved = value
        if index == "_numFriends": self._numFriends = value
        if index == "_showsTotalCount": self._showsTotalCount = value
        if index == "_showsWatchedCount": self._showsWatchedCount = value
        if index == "_showsLibraryCount": self._showsLibraryCount = value
        if index == "_showsShoutsCount": self._showsShoutsCount = value
        if index == "_showsLovedCount": self._showsLovedCount = value
        if index == "_episodesWatchedCount": self._episodesWatchedCount = value
        if index == "_episodesWatchedUniqueCount": self._episodesWatchedUniqueCount = value
        if index == "_episodesWatchedTraktCount": self._episodesWatchedTraktCount = value
        if index == "_episodesWatchedTraktUniqueCount": self._episodesWatchedTraktUniqueCount = value
        if index == "_episodesWatchedElsewhereCount": self._episodesWatchedElsewhereCount = value
        if index == "_episodesUnwatchedCount": self._episodesUnwatchedCount = value
        if index == "_episodesLibraryCount": self._episodesLibraryCount = value
        if index == "_episodesShoutsCount": self._episodesShoutsCount = value
        if index == "_episodesLovedCount": self._episodesLovedCount = value
        if index == "_moviesWatchedCount": self._moviesWatchedCount = value
        if index == "_moviesWatchedUniqueCount": self._moviesWatchedUniqueCount = value
        if index == "_moviesWatchedTraktCount": self._moviesWatchedTraktCount = value
        if index == "_moviesWatchedTraktUniqueCount": self._moviesWatchedTraktUniqueCount = value
        if index == "_moviesWatchedElsewhereCount": self._moviesWatchedElsewhereCount = value
        if index == "_moviesTotalCount": self._moviesTotalCount = value
        if index == "_moviesUnwatchedCount": self._moviesUnwatchedCount = value
        if index == "_moviesLibraryCount": self._moviesLibraryCount = value
        if index == "_moviesShoutsCount": self._moviesShoutsCount = value
        if index == "_moviesLovedCount": self._moviesLovedCount = value
    
    def save(self):
        trakt_cache.saveUser(self)
        
    @property
    def username(self):
        """. . ."""
        return self._username
        
    @property
    def protected(self):
        """. . ."""
        return self._protected
        
    @property
    def fullName(self):
        """. . ."""
        return self._fullName
        
    @property
    def gender(self):
        """. . ."""
        return self._gender
        
    @property
    def age(self):
        """. . ."""
        return self._age
        
    @property
    def location(self):
        """. . ."""
        return self._location
        
    @property
    def about(self):
        """. . ."""
        return self._about
        
    @property
    def joined(self):
        """. . ."""
        return self._joined
        
    @property
    def avatar(self):
        """. . ."""
        return self._avatar
        
    @property
    def url(self):
        """. . ."""
        return self._url
        
    @property
    def approved(self):
        """. . ."""
        return self._approved
        
    @property
    def numFriends(self):
        """. . ."""
        return self._numFriends
        
    @property
    def showsTotalCount(self):
        """. . ."""
        return self._showsTotalCount
        
    @property
    def showsWatchedCount(self):
        """. . ."""
        return self._showsWatchedCount
        
    @property
    def showsLibraryCount(self):
        """. . ."""
        return self._showsLibraryCount
        
    @property
    def showsShoutsCount(self):
        """. . ."""
        return self._showsShoutsCount
        
    @property
    def showsLovedCount(self):
        """. . ."""
        return self._showsLovedCount
        
    @property
    def episodesWatchedCount(self):
        """. . ."""
        return self._episodesWatchedCount
        
    @property
    def episodesWatchedUniqueCount(self):
        """. . ."""
        return self._episodesWatchedUniqueCount
        
    @property
    def episodesWatchedTraktCount(self):
        """. . ."""
        return self._episodesWatchedTraktCount
        
    @property
    def episodesWatchedTraktUniqueCount(self):
        """. . ."""
        return self._episodesWatchedTraktUniqueCount
        
    @property
    def episodesWatchedElsewhereCount(self):
        """. . ."""
        return self._episodesWatchedElsewhereCount
        
    @property
    def episodesUnwatchedCount(self):
        """. . ."""
        return self._episodesUnwatchedCount
        
    @property
    def episodesLibraryCount(self):
        """. . ."""
        return self._episodesLibraryCount
        
    @property
    def episodesShoutsCount(self):
        """. . ."""
        return self._episodesShoutsCount
        
    @property
    def episodesLovedCount(self):
        """. . ."""
        return self._episodesLovedCount
        
    @property
    def moviesWatchedCount(self):
        """. . ."""
        return self._moviesWatchedCount
        
    @property
    def moviesWatchedUniqueCount(self):
        """. . ."""
        return self._moviesWatchedUniqueCount
        
    @property
    def moviesWatchedTraktCount(self):
        """. . ."""
        return self._moviesWatchedTraktCount
        
    @property
    def moviesWatchedTraktUniqueCount(self):
        """. . ."""
        return self._moviesWatchedTraktUniqueCount
        
    @property
    def moviesWatchedElsewhereCount(self):
        """. . ."""
        return self._moviesWatchedElsewhereCount
        
    @property
    def moviesTotalCount(self):
        """. . ."""
        return self._moviesTotalCount
        
    @property
    def moviesUnwatchedCount(self):
        """. . ."""
        return self._moviesUnwatchedCount
        
    @property
    def moviesLibraryCount(self):
        """. . ."""
        return self._moviesLibraryCount
        
    @property
    def moviesShoutsCount(self):
        """. . ."""
        return self._moviesShoutsCount
        
    @property
    def moviesLovedCount(self):
        """. . ."""
        return self._moviesLovedCount
        
        
        
        
        
    @property
    def title(self):
        """The title of the movie."""
        trakt_cache.needSyncAtLeast(remoteIds = [self._remoteId])
        return self._title
        
    @property
    def year(self):
        """The year the movie was released."""
        trakt_cache.needSyncAtLeast(remoteIds = [self._remoteId])
        return self._year
        
    @property
    def runtime(self):
        """The number of minutes the movie runs for."""
        trakt_cache.needSyncAtLeast(remoteIds = [self._remoteId])
        return self._runtime
        
    @property
    def released(self):
        """The date the movie was released."""
        trakt_cache.needSyncAtLeast(remoteIds = [self._remoteId])
        return self._released
        
    @property
    def tagline(self):
        """A tag-line about the movie (like a catch phrase)."""
        trakt_cache.needSyncAtLeast(remoteIds = [self._remoteId])
        return self._tagline
        
    @property
    def overview(self):
        """An overview of the movie (like a plot)."""
        trakt_cache.needSyncAtLeast(remoteIds = [self._remoteId])
        return self._overview
        
    @property
    def classification(self):
        """The content classification indicating the suitible audience."""
        trakt_cache.needSyncAtLeast(remoteIds = [self._remoteId])
        return self._classification
        
    @property
    def trailer(self):
        """The movies trailer."""
        trakt_cache.needSyncAtLeast(remoteIds = [self._remoteId])
        return self._trailer
        
    @property
    def poster(self):
        """The movies poster image."""
        trakt_cache.needSyncAtLeast(remoteIds = [self._remoteId])
        return self._poster
        
    @property
    def fanart(self):
        """The movies fanart image."""
        trakt_cache.needSyncAtLeast(remoteIds = [self._remoteId])
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
    
    def Property(func):
        return property(**func()) 
    
    @property
    def rating(self):
        trakt_cache.needSyncAtLeast(remoteIds = [self._remoteId])
        return self._rating
    @rating.setter
    def rating(self, value):
        trakt_cache.makeChanges({'movies': [{'remoteId': self._remoteId, 'subject': 'rating', 'value': value}]}, traktOnly = True)
        
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
        trakt_cache.needSyncAtLeast(['movielibrary'], [self._remoteId])
        return self._libraryStatus
        
    @property
    def watchingStatus(self):
        """Whether the user is currently watching the movie."""
        raise NotImplementedError("This function has not been written")
        
    @property
    def watchlistStatus(self):
        """Whether the movie is in the users watchlist."""
        trakt_cache.needSyncAtLeast(['moviewatchlist'], [self._remoteId])
        return self._watchlistStatus
    @watchlistStatus.setter
    def watchlistStatus(self, value):
        raise NotImplementedError("This function has not been written")
        
    @property
    def recommendedStatus(self):
        """Whether the movie is recommended to the user by trakt."""
        trakt_cache.needSyncAtLeast(['movierecommended'], [self._remoteId])
        returnself._recommendedStatus
    
    @staticmethod
    def download(remoteId):
        Debug("[Movie] Downloading info for "+str(Movie.devolveId(remoteId)))
        local = getMovieFromTrakt(Movie.devolveId(remoteId))
        if local is None:
            movie = Movie(remoteId)
            movie._traktDbStatus = False
            return movie
        return Movie.fromTrakt(local)
    
    def traktise(self):
        movie = {}
        movie['title'] = self._title
        movie['year'] = self._year
        movie['plays'] = self._playcount
        movie['in_watchlist'] = self._watchlistStatus
        movie['in_collection'] = self._libraryStatus
        movie['runtime'] = self._runtime
        
        if str(self._remoteId).find('imdb=') == 0:
            movie['imdb_id'] = self._remoteId[5:]
        if str(self._remoteId).find('tmdb=') == 0:
            movie['tmdb_id'] = self._remoteId[5:]
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
        