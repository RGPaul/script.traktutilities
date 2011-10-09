# -*- coding: utf-8 -*-
# 

import xbmc,xbmcaddon,xbmcgui

from utilities import *
import notification_service
import trakt_cache

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
        notificationThread = notification_service.NotificationService()
        notificationThread.start()
        
        try:
            trakt_cache.init("special://profile/addon_data/script.TraktUtilities/trakt_cache")

        except SystemExit:
            notificationThread.abortRequested = True
            Debug("[Service] Auto sync processes aborted due to shutdown request")
            
        notificationThread.join()

autostart()
