# -*- coding: utf-8 -*-
# @author Ralph-Gordon Paul
# 

import xbmc,xbmcaddon,xbmcgui
from utilities import *

__settings__ = xbmcaddon.Addon( "script.TraktUtilities" )

Debug("service: " + __settings__.getAddonInfo("id") + " - version: " + __settings__.getAddonInfo("version"))

# starts update/sync
def autostart():
    if checkSettings(True):
        
        autosync_moviecollection = __settings__.getSetting("autosync_moviecollection")
        autosync_tvshowcollection = __settings__.getSetting("autosync_tvshowcollection")
        autosync_seenmovies = __settings__.getSetting("autosync_seenmovies")
        autosync_seentvshows = __settings__.getSetting("autosync_seentvshows")
        
        if autosync_moviecollection == "true":
            notification("Trakt Utilities", "start movie collection update...")
            updateMovieCollection(True)
        if autosync_tvshowcollection == "true":
            notification("Trakt Utilities", "start tvshow collection update...")
            updateTVShowCollection(True)
        if autosync_seenmovies == "true":
            Debug("autostart sync seen movies")
            notification("Trakt Utilities", "start sync seen movies...")
            syncSeenMovies(True)
        if autosync_seentvshows == "true":
            Debug("autostart sync seen tvshows")
            notification("Trakt Utilities", "start sync seen tvshows...")
            syncSeenTVShows(True)
            
        if autosync_moviecollection == "true" or autosync_tvshowcollection == "true" or autosync_seenmovies == "true" or autosync_seentvshows == "true":
            notification("Trakt Utilities", "update / sync done")
        
autostart()
