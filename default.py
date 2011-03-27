# -*- coding: utf-8 -*-
# @author Ralph-Gordon Paul
# 

import os
import xbmcgui,xbmcaddon,xbmc
from utilities import *

#read settings
__settings__ = xbmcaddon.Addon( "script.TraktUtilities" )
__language__ = __settings__.getLocalizedString

Debug("default: " + __settings__.getAddonInfo("id") + " - version: " + __settings__.getAddonInfo("version"))

# Usermenu:
def menu():

    # check if needed settings are set
    if checkSettings() == False:
        return

    options = [__language__(1210).encode( "utf-8", "ignore" ), __language__(1211).encode( "utf-8", "ignore" ), __language__(1212).encode( "utf-8", "ignore" ), __language__(1213).encode( "utf-8", "ignore" ), __language__(1214).encode( "utf-8", "ignore" ), __language__(1215).encode( "utf-8", "ignore" )]
    
    while True:
        select = xbmcgui.Dialog().select("Trakt Utilities ", options)
        Debug("Select: " + str(select))
        if select == -1:
            Debug ("menu quit by user")
            return
        else:
            if select == 0: # Update Movie Collection
                updateMovieCollection()
            elif select == 1: # Sync seen Movies
                syncSeenMovies()
            elif select == 2: # Update TVShow Collection
                updateTVShowCollection()
            elif select == 3: # Sync seen TVShows
                syncSeenTVShows()
            elif select == 4: # Clean Movie Collection
                cleanMovieCollection()
            elif select == 5: # Clean TVShow Collection
                cleanTVShowCollection()

menu()
