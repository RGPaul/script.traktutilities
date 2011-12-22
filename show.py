# -*- coding: utf-8 -*-
# 

import xbmc,xbmcaddon
import trakt_cache
from utilities import Debug

__author__ = "Ralph-Gordon Paul, Adrian Cowan"
__credits__ = ["Ralph-Gordon Paul", "Adrian Cowan", "Justin Nemeth",  "Sean Rudford"]
__license__ = "GPL"
__maintainer__ = "Ralph-Gordon Paul"
__email__ = "ralph-gordon.paul@uni-duesseldorf.de"
__status__ = "Production"

__settings__ = xbmcaddon.Addon( "script.TraktUtilities" )
__language__ = __settings__.getLocalizedString

# Caches all information between the add-on and the web based trakt api
class Show:
    
    def __init__(self, remoteId, static=False):
        if remoteId is None:
            raise ValueError("Must provide the id for the show")
        self._remoteId = str(remoteId)
        self._title = None
        self._year = None
        self._firstAired = None
        self._country = None
        self._overview = None
        self._runtime = None
        self._network = None
        self._airDay = None
        self._airTime = None
        self._classification = None
        self._rating = None
        self._watchlistStatus = None
        self._recommendedStatus = None
        self._libraryStatus = None
        self._traktDbStatus = None
        
        self._poster = None
        self._fanart = None
        
        self._episodes = {}
        
        self._bestBefore = {}
        self._static = static
    
    def __repr__(self):
        return "<"+repr(self._title)+" ("+str(self._year)+") - "+str(self._remoteId)+","+str(self._libraryStatus)+","+str(self._poster)+","+str(self._runtime)+">"
        
    def __str__(self):
        return unicode(self._title)+" ("+str(self._year)+")"
        
    def __getitem__(self, index):
        if index == "_title": return self._title
        if index == "_year": return self._year
        if index == "_firstAired": return self._firstAired
        if index == "_country": return self._country
        if index == "_overview": return self._overview
        if index == "_runtime": return self._runtime
        if index == "_network": return self._network
        if index == "_airDay": return self._airDay
        if index == "_airTime": return self._airTime
        if index == "_classification": return self._classification
        if index == "_rating": return self._rating
        if index == "_watchlistStatus": return self._watchlistStatus
        if index == "_recommendedStatus": return self._recommendedStatus
        if index == "_libraryStatus": return self._libraryStatus
        if index == "_poster": return self._poster
        if index == "_fanart": return self._fanart
        if index == "_episodes": return self._episodes
    
    def __setitem__(self, index, value):
        if index == "_title": self._title = value
        if index == "_year": self._year = value
        if index == "_firstAired": self._firstAired = value
        if index == "_country": self._country = value
        if index == "_overview": self._overview = value
        if index == "_runtime": self._runtime = value
        if index == "_network": self._network = value
        if index == "_airDay": self._airDay = value
        if index == "_airTime": self._airTime = value
        if index == "_classification": self._classification = value
        if index == "_rating": self._rating = value
        if index == "_watchlistStatus": self._watchlistStatus = value
        if index == "_recommendedStatus": self._recommendedStatus = value
        if index == "_libraryStatus": self._libraryStatus = value
        if index == "_poster": self._poster = value
        if index == "_fanart": self._fanart = value
        if index == "_episodes": self._episodes = value
    
    def save(self):
        TraktCache.saveShow(self)
    
    def refresh(self, property = None):
        if not self._static:
            trakt_cache.refreshShow(self._remoteId, property)
            self.reread()
        
    def reread(self):
        newer = trakt_cache.getShow(self._remoteId)
        
        self._title = newer._title
        self._year = newer._year
        self._firstAired = newer._firstAired
        self._country = newer._country
        self._overview = newer._overview
        self._runtime = newer._runtime
        self._network = newer._network
        self._airDay = newer._airDay
        self._airTime = newer._airTime
        self._classification = newer._classification
        self._rating = newer._rating
        self._watchlistStatus = newer._watchlistStatus
        self._recommendedStatus = newer._recommendedStatus
        self._libraryStatus = newer._libraryStatus
        self._traktDbStatus = newer._traktDbStatus
        
        self._poster = newer._poster
        self._fanart = newer._fanart
        
        self._episodes = newer._episodes
        
        self._bestBefore = newer._bestBefore
        self._static = newer._static
            
    @property
    def remoteId(self):
        """A unique identifier for the show."""
        return self._remoteId
        
    @property
    def title(self):
        """The title of the show."""
        self.checkExpire('title')
        return self._title
        
    @property
    def year(self):
        """The year the show was first aired."""
        self.checkExpire('year')
        return self._year
        
    @property
    def firstAired(self):
        """The date the show was first aired."""
        self.checkExpire('firstAired')
        return self._firstAired
        
    @property
    def country(self):
        """The country in which the show was first aired."""
        self.checkExpire('country')
        return self._country
        
    @property
    def overview(self):
        """An overview of the show (like a plot)."""
        self.checkExpire('overview')
        return self._overview
        
    @property
    def runtime(self):
        """The standard runtime of the show."""
        self.checkExpire('runtime')
        return self._runtime
        
    @property
    def network(self):
        """The TV network the show first aired on."""
        self.checkExpire('network')
        return self._network
        
    @property
    def airDay(self):
        """The day of the week that the show first airs."""
        self.checkExpire('airDay')
        return self._airDay
        
    @property
    def airTime(self):
        """The time of day that the show first airs."""
        self.checkExpire('airTime')
        return self._airTime
        
    @property
    def classification(self):
        """The content classification indicating the suitible audience."""
        self.checkExpire('classification')
        return self._classification
        
    @property
    def poster(self):
        """The shows poster image."""
        self.checkExpire('poster')
        return self._poster
        
    @property
    def fanart(self):
        """The shows fanart image."""
        self.checkExpire('fanart')
        return self._fanart
        
    def episodes(self, seasonFilter=None, episodeFilter=None):
        matches = []
        for season in self._episodes.keys:
            if season == seasonFilter or seasonFilter is None:
                for episode in self._episodes[season].keys:
                    if episode == episodeFilter or episodeFilter is None:
                        matches.append(getEpisode(self._remoteID, season+'x'+episode))
        return matches
        
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
        trakt_cache.makeChanges({'shows': [{'remoteId': self.remoteId, 'subject': 'rating', 'value': value}]}, traktOnly = True)
        
    @property
    def libraryStatus(self):
        """Whether the show is in the users library."""
        if not self._static: trakt_cache.needSyncAtLeast(['showlibrary'])
        return self._libraryStatus
        
    @property
    def watchingStatus(self):
        """Whether the user is currently watching the show."""
        raise NotImplementedError("This function has not been written")
        
    @property
    def watchlistStatus(self):
        """Whether the show is in the users watchlist."""
        if not self._static: trakt_cache.needSyncAtLeast(['showwatchlist'])
        return self._watchlistStatus
    @watchlistStatus.setter
    def watchlistStatus(self, value):
        raise NotImplementedError("This function has not been written")
        
    @property
    def recommendedStatus(self):
        """Whether the show is recommended to the user by trakt."""
        if not self._static: trakt_cache.needSyncAtLeast(['showrecommended'])
        returnself._recommendedStatus
    
    def checkExpire(self, property):
        if self._static:
            return
        if property not in self._bestBefore or self._bestBefore[property] < time.time():
            self.refresh(property)
        
    @staticmethod
    def download(remoteId):
        Debug("[Show] Downloading info for "+str(Show.devolveId(remoteId)))
        local = Trakt.showSummary(Show.devolveId(remoteId))
        if local is None:
            show = Show(remoteId)
            show._traktDbStatus = False
            return movie
        return Show.fromTrakt(local)
        
    def traktise(self):
        show = {}
        show['title'] = _title
        show['year'] = _year
        show['plays'] = _playcount
        show['in_watchlist'] = _watchlistStatus
        show['in_collection'] = _libraryStatus
        if str(_remoteId).find('tvbd=') == 0:
            show['tvdb_id'] = _remoteId[5:]
        if str(_remoteId).find('imbd=') == 0:
            show['imdb_id'] = _remoteId[5:]
        return show
        
    @staticmethod
    def fromTrakt(show, static = True):
        if show is None: return None
        if 'tvdb_id' in show:
            local = Show("tvdb="+show['tvdb_id'], static)
        elif 'imdb_id' in movie:
            local = Show("imdb="+show['imdb_id'], static)
        else:
            return None
        local._title = show['title']
        local._year = show['year']
        if 'url' in show:
            local._playcount = show['url']
        if 'in_watchlist' in show:
            local._watchlistStatus = show['in_watchlist']
        if 'in_collection' in show:
            local._libraryStatus = show['in_collection']
        if 'images' in show and 'poster' in show['images']:
            local._poster = show['images']['poster']
        if 'images' in show and 'fanart' in show['images']:
            local._fanart = show['images']['fanart']
        if 'first_aired' in show:
            local._firstAired = show['first_aired']
        if 'coutnry' in show:
            local._coutnry = show['coutnry']
        if 'network' in show:
            local._network = show['network']
        if 'runtime' in show:
            local._runtime = show['runtime']
        if 'air_day' in show:
            local._airDay = show['air_day']
        if 'air_time' in show:
            local._airTime = show['air_time']
        if 'tagline' in show:
            local._tagline = show['tagline']
        if 'overview' in show:
            local._overview = show['overview']
        if 'certification' in show:
            local._classification = show['certification']
        return local
        
    @staticmethod
    def fromXbmc(show, static = True):
        if show is None: return None
        if 'imdbnumber' not in show or show['imdbnumber'] is None or show['imdbnumber'].strip() == "":
            Debug("[~] "+repr(show))
            remoteId = trakt_cache.getShowRemoteId(show['showid'])
            if remoteId is not None:
                local = Show(remoteId, static)
            else:
                tvdb_id = searchGoogleForTvdbId(unicode(Show['title'])+"+"+unicode(Show['year']))
                if tvdb_id is None or tvdb_id == "":
                    traktShow = searchTraktForShow(show['title'], show['year'])
                    if traktShow is None:
                         Debug("[Show] Unable to find show '"+unicode(show['title'])+"' ["+unicode(show['year'])+"]")
                    else:
                        if 'tvdb_id' in traktMovie and traktMovie['tvdb_id'] <> "":
                            local = Show("tvdb="+traktMovie['tvdb_id'], static)
                        elif 'imdb_id' in traktMovie and traktMovie['imdb_id'] <> "":
                            local = Show("imdb="+traktMovie['imdb_id'], static)
                        else:
                            return None
                    return None
                else:
                    local = Show("tvdb="+tvdb_id, static)
        else:
            local = Show(Show.evolveId(show['imdbnumber']), static)
        trakt_cache.relateShowId(show['tvshowid'], local._remoteId)
        if local._remoteId == 'tvdb=' or local._remoteId == 'imdb=':
            Debug("[Show] Fail tried to use blank remote id for "+repr(show))
            return None
        if 'title' in show: local._title = show['title']
        if 'year' in show: local._year = show['year']
        if 'runtime' in show: local._runtime = show['runtime']
        return local
    
    @staticmethod
    def evolveId(idString):
        if idString.find('tt') == 0:
            return str("imdb="+idString.strip())
        else:
            return str("tvdb="+idString.strip())
    
    @staticmethod
    def devolveId(idString):
        if idString.find('imdb=tt') == 0:
            return idString[5:]
        elif idString.find('imdb=') == 0:
            return "tt"+idString[5:]
        elif idString.find('tvdb=') == 0:
            return idString[5:]