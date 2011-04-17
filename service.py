# -*- coding: utf-8 -*-
# 

import xbmc,xbmcaddon,xbmcgui
import telnetlib, time, simplejson
from utilities import *
from rating import *
from sync_update import *

__author__ = "Ralph-Gordon Paul, Adrian Cowan"
__credits__ = ["Ralph-Gordon Paul", "Adrian Cowan", "Justin Nemeth",  "Sean Rudford"]
__license__ = "GPL"
__maintainer__ = "Ralph-Gordon Paul"
__email__ = "ralph-gordon.paul@uni-duesseldorf.de"
__status__ = "Production"

__settings__ = xbmcaddon.Addon( "script.TraktUtilities" )
__language__ = __settings__.getLocalizedString

Debug("service: " + __settings__.getAddonInfo("id") + " - version: " + __settings__.getAddonInfo("version"))

# starts update/sync
def autostart():
    if checkSettings(True):
        
        autosync_moviecollection = __settings__.getSetting("autosync_moviecollection")
        autosync_tvshowcollection = __settings__.getSetting("autosync_tvshowcollection")
        autosync_seenmovies = __settings__.getSetting("autosync_seenmovies")
        autosync_seentvshows = __settings__.getSetting("autosync_seentvshows")
        
        if autosync_moviecollection == "true":
            notification("Trakt Utilities", __language__(1180).encode( "utf-8", "ignore" )) # start movie collection update
            updateMovieCollection(True)
        if autosync_tvshowcollection == "true":
            notification("Trakt Utilities", __language__(1181).encode( "utf-8", "ignore" )) # start tvshow collection update
            updateTVShowCollection(True)
        if autosync_seenmovies == "true":
            Debug("autostart sync seen movies")
            notification("Trakt Utilities", __language__(1182).encode( "utf-8", "ignore" )) # start sync seen movies
            syncSeenMovies(True)
        if autosync_seentvshows == "true":
            Debug("autostart sync seen tvshows")
            notification("Trakt Utilities", __language__(1183).encode( "utf-8", "ignore" )) # start sync seen tv shows
            syncSeenTVShows(True)
            
        if autosync_moviecollection == "true" or autosync_tvshowcollection == "true" or autosync_seenmovies == "true" or autosync_seentvshows == "true":
            notification("Trakt Utilities", __language__(1184).encode( "utf-8", "ignore" )) # update / sync done
    
    tn = telnetlib.Telnet('localhost', 9090, 10)
    
    while (not xbmc.abortRequested):
        try:
            raw = tn.read_until("\n")
            data = json.loads(raw)
            if 'params' in data:
                if 'message' in data['params']:
                    if data['params']['message'] == 'NewPlayCount':
                        if 'sender' in data['params']:
                            if data['params']['sender'] == 'xbmc':
                                if 'data' in data['params']:
                                    if 'movieid' in data['params']['data']:
                                        doRate(data['params']['data']['movieid'])
        except EOFError:
            tn.open('localhost', 9090, 10)
            time.sleep(1)
        
autostart()
