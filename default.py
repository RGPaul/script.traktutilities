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
    if sys.argv[2].find('?view=') == 0:
        windowName = sys.argv[2][6:]
        Debug("Requesting display of window "+repr(windowName))
        if windowName in ('watchlistMovies', 'watchlistShows', 'trendingMovies', 'trendingShows', 'recommendedMovies', 'recommendedShows'):
            rpccmd = json.dumps({'jsonrpc': '2.0', 'method': 'JSONRPC.NotifyAll','params':{'sender': 'TraktUtilities', 'message': 'TraktUtilities.View', 'data':windowName}, 'id': 1})
            Debug("[~] "+repr(rpccmd))
            result = xbmc.executeJSONRPC(rpccmd)
            result = json.loads(result)
        return
    if sys.argv[2].find('?sync=') == 0:
        setName = sys.argv[2][6:]
        Debug("Requesting sync of set "+repr(setName))
        rpccmd = json.dumps({'jsonrpc': '2.0', 'method': 'JSONRPC.NotifyAll','params':{'sender': 'TraktUtilities', 'message': 'TraktUtilities.Sync', 'data':setName}, 'id': 1})
        result = xbmc.executeJSONRPC(rpccmd)
        result = json.loads(result)
        return
    menu()

def submenu(menuName, title):
    li = xbmcgui.ListItem(title)
    url = sys.argv[0]+'?menu=' + str(menuName)
    return url, li, True
    
def view(windowName, title):
    li = xbmcgui.ListItem(title)
    url = sys.argv[0]+'?view=' + str(windowName)
    return url, li, False

def sync(setName, title):
    li = xbmcgui.ListItem(title)
    url = sys.argv[0]+'?sync=' + str(setName)
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
        sync('movielibrary', __language__(1217).encode( "utf-8", "ignore" )),
        sync('movielibrary', __language__(1218).encode( "utf-8", "ignore" )),
        sync('showlibrary', __language__(1219).encode( "utf-8", "ignore" )),
        sync('showlibrary', __language__(1220).encode( "utf-8", "ignore" ))]
        
    xbmcplugin.addDirectoryItems(int(sys.argv[1]), options)
    
    xbmcplugin.endOfDirectory(handle=int(sys.argv[1]), succeeded=True)

def submenuTrendingMoviesTVShows():
    options = [
        view('trendingMovies', __language__(1250).encode( "utf-8", "ignore" )),
        view('trendingTVShows', __language__(1251).encode( "utf-8", "ignore" ))]
        
    xbmcplugin.addDirectoryItems(int(sys.argv[1]), options)
    
    xbmcplugin.endOfDirectory(handle=int(sys.argv[1]), succeeded=True)

def submenuWatchlist():
    options = [
        view('watchlistMovies', __language__(1252).encode( "utf-8", "ignore" )),
        view('watchlistTVShows', __language__(1253).encode( "utf-8", "ignore" ))]
        
    xbmcplugin.addDirectoryItems(int(sys.argv[1]), options)
    
    xbmcplugin.endOfDirectory(handle=int(sys.argv[1]), succeeded=True)

def submenuRecommendations():
    options = [
        view('recommendedMovies', __language__(1255).encode( "utf-8", "ignore" )),
        view('recommendedTVShows', __language__(1256).encode( "utf-8", "ignore" ))]
        
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