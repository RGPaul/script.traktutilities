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
        responce = getEpisodeFromXbmc(data['params']['data']['id'])
        if responce == None: return
        info = responce['episodedetails']
        Debug("Instant-sync (episode playcount): "+str(info))
        if data['params']['data']['playcount'] == 0:
            res = setEpisodesUnseenOnTrakt(None, info['showtitle'], None, [{'season':info['season'], 'episode':info['episode']}])
        elif data['params']['data']['playcount'] == 1:
            res = setEpisodesSeenOnTrakt(None, info['showtitle'], None, [{'season':info['season'], 'episode':info['episode']}])
        Debug("Instant-sync (episode playcount): responce "+str(res))