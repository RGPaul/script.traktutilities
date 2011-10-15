# -*- coding: utf-8 -*-
# 

import sys
import os
import xbmcgui,xbmcaddon,xbmc,xbmcplugin
from utilities import *
from friends import *
from trakt import Trakt

try: import simplejson as json
except ImportError: import json

__author__ = "Ralph-Gordon Paul, Adrian Cowan"
__credits__ = ["Ralph-Gordon Paul", "Justin Nemeth",  "Sean Rudford"]
__license__ = "GPL"
__maintainer__ = "Ralph-Gordon Paul"
__email__ = "ralph-gordon.paul@uni-duesseldorf.de"
__status__ = "Production"

#read settings
__settings__ = xbmcaddon.Addon( "script.TraktUtilities" )
__language__ = __settings__.getLocalizedString

Debug("default: " + __settings__.getAddonInfo("id") + " - version: " + __settings__.getAddonInfo("version"))

def switchBoard():
    Debug("[Default] Request: "+repr(sys.argv))
    if len(sys.argv[2]) == 0:
        menu()
        return
    if sys.argv[2].find('?menu=') == 0:
        menuName = sys.argv[2][6:]
        Debug(str(menuName))
        if menuName == 'menu':
            menu()
        elif menuName == 'watchlist':
            submenuWatchlist()
        elif menuName == 'friends':
            showFriends()
        elif menuName == 'recommendations':
            submenuRecommendations()
        elif menuName == 'trending':
            submenuTrendingMoviesTVShows()
        elif menuName == 'updateSyncClean':
            submenuUpdateSyncClean()
        elif menuName == 'testing':
            testing()
        else:
            menu()
        return
    if sys.argv[2].find('?action=') == 0:
        actionName = sys.argv[2][8:]
        Debug(str(actionName))
        if actionName == 'watchlistMovies':
            rpccmd = json.dumps({'jsonrpc': '2.0', 'method': 'JSONRPC.NotifyAll','params':{'sender': 'TraktUtilities', 'message': 'TraktUtilities.Show.MoviesWatchlist', 'data':{}}, 'id': 1})
            result = xbmc.executeJSONRPC(rpccmd)
            result = json.loads(result)
        elif actionName == 'watchlistTVShows':
            showWatchlistTVShows()
        elif actionName == 'trendingMovies':
            showTrendingMovies()
        elif actionName == 'trendingTVShows':
            showTrendingTVShows()
        elif actionName == 'recommendedMovies':
            showRecommendedMovies()
        elif actionName == 'recommendedTVShows':
            showRecommendedTVShows()
        elif actionName == 'updateMovieCollection':
            showWatchlistTVShows()
        elif actionName == 'syncSeenMovies':
            syncSeenMovies()
        elif actionName == 'updateTVShowCollection':
            updateTVShowCollection()
        elif actionName == 'syncSeenTVShows':
            syncSeenTVShows()
        elif actionName == 'cleanMovieCollection':
            cleanMovieCollection()
        elif actionName == 'cleanTVShowCollection':
            cleanTVShowCollection()
        else:
            menu()
        return
    menu()

def submenu(menuName, title):
    li = xbmcgui.ListItem(title)
    url = sys.argv[0]+'?menu=' + str(menuName)
    return url, li, True
    
def action(actionName, title):
    li = xbmcgui.ListItem(title)
    url = sys.argv[0]+'?action=' + str(actionName)
    return url, li, False

# Usermenu:
def menu():
    options = [
        submenu('watchlist', __language__(1210).encode( "utf-8", "ignore" )),
        submenu('friends', __language__(1211).encode( "utf-8", "ignore" )),
        submenu('recommendations', __language__(1212).encode( "utf-8", "ignore" )),
        submenu('trending', __language__(1213).encode( "utf-8", "ignore" )),
        submenu('updateSyncClean', __language__(1214).encode( "utf-8", "ignore" ))]
        
    if __settings__.getSetting("debug"):
        options.append(submenu('testing', "Testing [Employees only]"))
        
    xbmcplugin.addDirectoryItems(int(sys.argv[1]), options)
    
    xbmcplugin.endOfDirectory(handle=int(sys.argv[1]), succeeded=True)

def submenuUpdateSyncClean():
    options = [
        action('updateMovieCollection', __language__(1217).encode( "utf-8", "ignore" )),
        action('syncSeenMovies', __language__(1218).encode( "utf-8", "ignore" )),
        action('updateTVShowCollection', __language__(1219).encode( "utf-8", "ignore" )),
        action('syncSeenTVShows', __language__(1220).encode( "utf-8", "ignore" )),
        action('cleanMovieCollection', __language__(1221).encode( "utf-8", "ignore" )),
        action('cleanTVShowCollection', __language__(1222).encode( "utf-8", "ignore" ))]
        
    xbmcplugin.addDirectoryItems(int(sys.argv[1]), options)
    
    xbmcplugin.endOfDirectory(handle=int(sys.argv[1]), succeeded=True)

def submenuTrendingMoviesTVShows():
    options = [
        action('trendingMovies', __language__(1250).encode( "utf-8", "ignore" )),
        action('trendingTVShows', __language__(1251).encode( "utf-8", "ignore" ))]
        
    xbmcplugin.addDirectoryItems(int(sys.argv[1]), options)
    
    xbmcplugin.endOfDirectory(handle=int(sys.argv[1]), succeeded=True)

def submenuWatchlist():
    options = [
        action('watchlistMovies', __language__(1252).encode( "utf-8", "ignore" )),
        action('watchlistTVShows', __language__(1253).encode( "utf-8", "ignore" ))]
        
    xbmcplugin.addDirectoryItems(int(sys.argv[1]), options)
    
    xbmcplugin.endOfDirectory(handle=int(sys.argv[1]), succeeded=True)

def submenuRecommendations():
    options = [
        action('recommendedMovies', __language__(1255).encode( "utf-8", "ignore" )),
        action('recommendedTVShows', __language__(1256).encode( "utf-8", "ignore" ))]
        
    xbmcplugin.addDirectoryItems(int(sys.argv[1]), options)
    
    xbmcplugin.endOfDirectory(handle=int(sys.argv[1]), succeeded=True)


def testing():
    Trakt.testAll()
    """movie = Movie("dummy=1234455")
    Debug("[~] rating: "+str(movie.rating))
    movie.rating = "help"
    movie.setRating("help")
    Debug('[TraktCache] _updateTrakt, libraryStatus, unlibrary, responce: '+str(result))
    Debug(str(trakt_cache.getMovieWatchList()))"""
    xbmcgui.Dialog().ok("Trakt Utilities, TESTS", "Success")
    
if __name__ == "__main__" :
    switchBoard()