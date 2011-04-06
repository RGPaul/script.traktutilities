# -*- coding: utf-8 -*-
# @author Ralph-Gordon Paul
# 

import os
import xbmcgui,xbmcaddon,xbmc
from utilities import *
from sync_update import *

#read settings
__settings__ = xbmcaddon.Addon( "script.TraktUtilities" )
__language__ = __settings__.getLocalizedString

Debug("default: " + __settings__.getAddonInfo("id") + " - version: " + __settings__.getAddonInfo("version"))

# Usermenu:
def menu():

    # check if needed settings are set
    if checkSettings() == False:
        return

    options = [__language__(1210).encode( "utf-8", "ignore" ), __language__(1213).encode( "utf-8", "ignore" ), __language__(1217).encode( "utf-8", "ignore" ), __language__(1218).encode( "utf-8", "ignore" ), __language__(1219).encode( "utf-8", "ignore" ), __language__(1220).encode( "utf-8", "ignore" ), __language__(1221).encode( "utf-8", "ignore" ), __language__(1222).encode( "utf-8", "ignore" )]
    
    while True:
        select = xbmcgui.Dialog().select("Trakt Utilities", options)
        Debug("Select: " + str(select))
        if select == -1:
            Debug ("menu quit by user")
            return
        else:
            if select == 0: # Watchlist
                pass
                #showWatchlist()
            elif select == 1: # Trending Movies / TV Shows
                submenuTrendingMoviesTVShows()
            elif select == 2: # Update Movie Collection
                updateMovieCollection()
            elif select == 3: # Sync seen Movies
                syncSeenMovies()
            elif select == 4: # Update TV Show Collection
                updateTVShowCollection()
            elif select == 5: # Sync seen TV Shows
                syncSeenTVShows()
            elif select == 6: # Clean Movie Collection
                cleanMovieCollection()
            elif select == 7: # Clean TV Show Collection
                cleanTVShowCollection()
                
def submenuTrendingMoviesTVShows():

    options = [__language__(1250).encode( "utf-8", "ignore" ), __language__(1251).encode( "utf-8", "ignore" )]
    
    while True:
        select = xbmcgui.Dialog().select(__language__(1213).encode( "utf-8", "ignore" ), options)
        Debug("Select: " + str(select))
        if select == -1:
            Debug ("menu quit by user")
            return
        if select == 0: # Trending Movies
            pass
            #showTrendingMovies()
        elif select == 1: # Trending TV Shows
            pass
            #showTrendingTVShows()
        

menu()
