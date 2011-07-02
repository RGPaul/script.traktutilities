# -*- coding: utf-8 -*-
# 

import xbmc,xbmcaddon,xbmcgui
import telnetlib, time
import simplejson as json
import threading
from utilities import *
from instant_sync import *

__author__ = "Ralph-Gordon Paul, Adrian Cowan"
__credits__ = ["Ralph-Gordon Paul", "Adrian Cowan", "Justin Nemeth",  "Sean Rudford"]
__license__ = "GPL"
__maintainer__ = "Ralph-Gordon Paul"
__email__ = "ralph-gordon.paul@uni-duesseldorf.de"
__status__ = "Production"

__settings__ = xbmcaddon.Addon( "script.TraktUtilities" )
__language__ = __settings__.getLocalizedString

# Move this to its own file
def instantSyncPlayCount(data):
    if data['params']['data']['type'] == 'episode':
        info = getEpisodeDetailsFromXbmc(data['params']['data']['id'], ['showtitle', 'season', 'episode'])
        if info == None: return
        Debug("Instant-sync (episode playcount): "+str(info))
        if data['params']['data']['playcount'] == 0:
            res = setEpisodesUnseenOnTrakt(None, info['showtitle'], None, [{'season':info['season'], 'episode':info['episode']}])
        elif data['params']['data']['playcount'] == 1:
            res = setEpisodesSeenOnTrakt(None, info['showtitle'], None, [{'season':info['season'], 'episode':info['episode']}])
        Debug("Instant-sync (episode playcount): responce "+str(res))
    if data['params']['data']['type'] == 'movie':
        info = getMovieDetailsFromXbmc(data['params']['data']['id'], ['imdbnumber', 'title', 'year', 'playcount', 'lastplayed'])
        if info == None: return
        Debug("Instant-sync (movie playcount): "+str(info))
        if 'lastplayed' not in info: info['lastplayed'] = None
        if data['params']['data']['playcount'] == 0:
            res = setMoviesUnseenOnTrakt([{'imdb_id':info['imdbnumber'], 'title':info['title'], 'year':info['year'], 'plays':data['params']['data']['playcount'], 'last_played':info['lastplayed']}])
        elif data['params']['data']['playcount'] == 1:
            res = setMoviesSeenOnTrakt([{'imdb_id':info['imdbnumber'], 'title':info['title'], 'year':info['year'], 'plays':data['params']['data']['playcount'], 'last_played':info['lastplayed']}])
        Debug("Instant-sync (movie playcount): responce "+str(res))