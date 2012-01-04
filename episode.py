# -*- coding: utf-8 -*-
# 

import xbmc,xbmcaddon
from utilities import *
import trakt_cache
from show import Show
from trakt import Trakt

__author__ = "Ralph-Gordon Paul, Adrian Cowan"
__credits__ = ["Ralph-Gordon Paul", "Adrian Cowan", "Justin Nemeth",  "Sean Rudford"]
__license__ = "GPL"
__maintainer__ = "Ralph-Gordon Paul"
__email__ = "ralph-gordon.paul@uni-duesseldorf.de"
__status__ = "Production"

__settings__ = xbmcaddon.Addon( "script.TraktUtilities" )
__language__ = __settings__.getLocalizedString

# Caches all information between the add-on and the web based trakt api
class Episode(object):
    
    def __init__(self, remoteId, static=False):
        if remoteId is None:
            raise ValueError("Must provide the id for the episode")
        self._remoteId = str(remoteId)
        self._showRemoteId = str(remoteId)[:str(remoteId).rfind('@')]
        self._season = int(str(remoteId)[str(remoteId).rfind('@')+1:str(remoteId).rfind('x')])
        self._episode = int(str(remoteId)[str(remoteId).rfind('x')+1:])
        if not static:
            if self.reread():
                return
                
        self._title = None
        self._overview = None
        self._firstAired = None
        self._playcount = None
        self._rating = None
        self._watchlistStatus = None
        self._libraryStatus = None
        self._traktDbStatus = None
        
        self._screen = None
        
        self._bestBefore = {}
        self._static = static
            
        
    def __repr__(self):
        return "<"+repr(self._title)+" - "+str(self._remoteId)+","+str(self._libraryStatus)+","+str(self._screen)+","+str(self._overview)+">"
        
    def __str__(self):
        return unicode(self._title)
    
    def __getitem__(self, index):
        if index == "_title": return self._title
        if index == "_overview": return self._overview
        if index == "_playcount": return self._playcount
        if index == "_rating": return self._rating
        if index == "_firstAired": return self._firstAired
        if index == "_watchlistStatus": return self._watchlistStatus
        if index == "_libraryStatus": return self._libraryStatus
        if index == "_screen": return self._screen
        if index == "_fanart": return self._fanart
    
    def __setitem__(self, index, value):
        if index == "_title": self._title = value
        if index == "_overview": self._overview = value
        if index == "_classification": self._classification = value
        if index == "_playcount": self._playcount = value
        if index == "_rating": self._rating = value
        if index == "_firstAired": self._firstAired = value
        if index == "_watchlistStatus": self._watchlistStatus = value
        if index == "_libraryStatus": self._libraryStatus = value
        if index == "_screen": return self._screen
        if index == "_fanart": self._fanart = value
    
    
    def save(self):
        self._static = False
        trakt_cache.saveEpisode(self)
        
    def refresh(self, property = None):
        if not self._static:
            trakt_cache.refreshEpisode(self._remoteId, property)
            self.reread()
            
    def reread(self):
        newer = trakt_cache.getEpisode(self._remoteId)
        if newer is None:
            return False
        
        self._title = newer._title
        self._overview = newer._overview
        self._firstAired = newer._firstAired
        self._playcount = newer._playcount
        self._rating = newer._rating
        self._watchlistStatus = newer._watchlistStatus
        self._libraryStatus = newer._libraryStatus
        self._traktDbStatus = newer._traktDbStatus
        
        self._screen = newer._screen
        
        self._bestBefore = newer._bestBefore
        self._static = newer._static
        
        return True
        
    @property
    def remoteId(self):
        """A unique identifier for the show."""
        return self._remoteId
        
    @property
    def season(self):
        """The seson number of the episode."""
        return self._remoteId
        
    @property
    def episode(self):
        """The episode number of the episode."""
        return self._remoteId
        
    @property
    def title(self):
        """The title of the episode."""
        self.checkExpire('title')
        return self._title
        
    @property
    def overview(self):
        """An overview of the episode (like a plot)."""
        self.checkExpire('overview')
        return self._overview
        
    @property
    def firstAired(self):
        """The date the episode was first aired."""
        self.checkExpire('firstAired')
        return self._firstAired
        
    @property
    def screen(self):
        """The episodes screen image (screenshot / screencap)."""
        self.checkExpire('screen')
        return self._screen
        
    def scrobble(self, progress):
        raise NotImplementedError("This function has not been written")
    def shout(self, text):
        raise NotImplementedError("This function has not been written")
    def watching(self, progress):
        raise NotImplementedError("This function has not been written")
    @staticmethod
    def cancelWatching():
        raise NotImplementedError("This function has not been written")
    def play(self):
        raise NotImplementedError("This function has not been written")
    
    def Property(func):
        return property(**func()) 
    
    @property
    def rating(self):
        self.checkExpire('rating')
        return self._rating
    @rating.setter
    def rating(self, value):
        trakt_cache.makeChanges({'episodes': [{'remoteId': self._remoteId, 'subject': 'rating', 'value': value}]}, traktOnly = True)
        
    @property
    def playcount(self):
        """How many time the user has watched the episode."""
        self.checkExpire('playcount')
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
    
    def checkExpire(self, property):
        if self._static:
            return
        if property not in self._bestBefore or self['_'+str(property)] is None or self._bestBefore[property] < time.time():
            self.refresh(property)
    
    def getShow(self):
        return trakt_cache.getShow(self.showRemoteId)
        
    @staticmethod
    def download(remoteId):
        showRemoteId, season, episode = Episode.devolveId(remoteId)
        Debug("[Episode] Downloading info for "+str(showRemoteId)+" "+str(season)+"x"+str(episode))
        local = Trakt.showEpisodeSummary(showRemoteId, season, episode)
        if local is None:
            episode = Episode(str(showRemoteId)+'@'+str(season)+'x'+str(episode), static=True)
            episode._traktDbStatus = False
            return episode
        return Episode.fromTrakt(local['show'], local['episode'])
    
    def traktise(self):
        show = Show(self._showRemoteId)
        episode = {}
        
        episode['title'] = self._title
        episode['showtitle'] = show._title
        episode['year'] = show._year
        episode['season'] = self._season
        episode['episode'] = self._episode
        episode['plays'] = self._playcount
        episode['in_watchlist'] = self._watchlistStatus
        episode['in_collection'] = self._libraryStatus
        
        episode['imdb_id'] = None
        episode['tvdb_id'] = None
        if str(self._remoteId).find('imdb=') == 0:
            episode['imdb_id'] = Episode.devolveId(self._remoteId)[0]
        if str(self._remoteId).find('tvdb=') == 0:
            episode['tvdb_id'] = Episode.devolveId(self._remoteId)[0]
        return episode
        
    @staticmethod
    def fromTrakt(show, episode, static = True):
        if show is None or episode is None: return None
        if 'season' not in episode or 'number' not in episode: return None 
        if 'tvdb_id' in show:
            local = Episode("tvdb="+str(show['tvdb_id'])+'@'+str(episode['season'])+'x'+str(episode['number']), static)
        elif 'imdb_id' in show:
            local = Episode("imdb="+str(show['imdb_id'])+'@'+str(episode['season'])+'x'+str(episode['number']), static)
        else:
            return None
        local._title = episode['title']
        if 'plays' in episode:
            local._playcount = episode['plays']
        if 'in_watchlist' in episode:
            local._watchlistStatus = episode['in_watchlist']
        if 'in_collection' in episode:
            local._libraryStatus = episode['in_collection']
        if 'images' in episode and 'screen' in episode['images']:
            local._screen = episode['images']['screen']
        if 'firstAired' in episode:
            local._runtime = episode['first_aired']
        if 'overview' in episode:
            local._overview = episode['overview']
            
        return local
     
    @staticmethod
    def fromXbmc(remoteId, episode, static = True):
        if remoteId is None or episode is None: return None
        if 'season' not in episode or 'episode' not in episode: return None
        
        if remoteId == 'imdb=' or remoteId == 'tmdb=':
            Debug("[Movie] Fail tried to use blank remote id for "+repr(movie))
            return None
            
        local = Episode(str(remoteId)+'@'+str(episode['season'])+'x'+str(episode['episode']), static)
        trakt_cache.relateEpisodeId(episode['episodeid'], str(remoteId)+'@'+str(episode['season'])+'x'+str(episode['episode']))
        if 'title' in episode: local._title = episode['title']
        if 'firstaired' in episode: local._firstAired = episode['firstaired']
        if 'playcount' in episode: local._playcount = episode['playcount']
        if 'rating' in episode: local._rating = episode['rating']
        return local
     
    @staticmethod
    def evolveId(idString, season, episode):
        if idString.find('tt') == 0:
            return str("imdb="+idString.strip()+'@'+str(season)+'x'+str(episode))
        else:
            return str("tvdb="+idString.strip()+'@'+str(season)+'x'+str(episode))
    
    @staticmethod
    def devolveId(idString):
        div1 = idString.rfind('@')
        div2 = idString.rfind('x')
        if idString.find('imdb=tt') == 0:
            return idString[5:div1], int(idString[div1+1:div2]), int(idString[div2+1:])
        elif idString.find('imdb=') == 0:
            return "tt"+idString[5:div1], int(idString[div1+1:div2]), int(idString[div2+1:])
        elif idString.find('tvdb=') == 0:
            return idString[5:div1], int(idString[div1+1:div2]), int(idString[div2+1:])   
    
    @staticmethod
    def splitId(idString):
        div1 = idString.rfind('@')
        div2 = idString.rfind('x')
        return idString[:div1], int(idString[div1+1:div2]), int(idString[div2+1:])