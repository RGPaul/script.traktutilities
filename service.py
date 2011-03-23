# -*- coding: utf-8 -*-
# @author Ralph-Gordon Paul
# 

import xbmc,xbmcaddon,xbmcgui
from utilities import *

__settings__ = xbmcaddon.Addon( "script.TraktUtilities" )

Debug("id: " + __settings__.getAddonInfo("id") + " - version: " + __settings__.getAddonInfo("version"))

"""
Debug ("SERVICE: " + os.getcwd())

autosync_moviecollection = __settings__.getSetting("autosync_moviecollection")
autosync_tvshowcollection = __settings__.getSetting("autosync_tvshowcollection")
autosync_seenmovies = __settings__.getSetting("autosync_seenmovies")
autosync_seentvshows = __settings__.getSetting("autosync_seentvshows")
"""
# check for update at startup
def checkForUpdates():
    pass # Todo

# starts update/sync
# Todo: really implement
def autostart():
    pass
    """
    if checkSettings(True):
        if autosync_moviecollection:
            notification("Trakt Utilities", "start movie collection update...")
            #updateMovieCollection(True)
        if autosync_tvshowcollection:
            notification("Trakt Utilities", "start tvshow collection update...")
            #updateTVShowCollection(True)
        if autosync_seenmovies:
            notification("Trakt Utilities", "start sync seen movies...")
            #syncSeenMovies(True)
        if autosync_seentvshows:
            notification("Trakt Utilities", "start sync seen tvshows...")
            #syncSeenTVShows(True)
        if autosync_moviecollection or autosync_tvshowcollection or autosync_seenmovies or autosync_seentvshows:
            notification("Trakt Utilities", "update / sync done")
    """
    
#autostart()
