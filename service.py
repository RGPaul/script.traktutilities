# -*- coding: utf-8 -*-
# 

import xbmc,xbmcaddon,xbmcgui

from utilities import *
import notification_service
import trakt_cache
import time
from async_tools import Pool

__author__ = "Ralph-Gordon Paul, Adrian Cowan"
__credits__ = ["Ralph-Gordon Paul", "Adrian Cowan", "Justin Nemeth",  "Sean Rudford"]
__license__ = "GPL"
__maintainer__ = "Ralph-Gordon Paul"
__email__ = "ralph-gordon.paul@uni-duesseldorf.de"
__status__ = "Production"

__settings__ = xbmcaddon.Addon( "script.TraktUtilities" )
__language__ = __settings__.getLocalizedString

Debug("service: " + __settings__.getAddonInfo("id") + " - version: " + __settings__.getAddonInfo("version"))

cacheDirectory = "special://profile/addon_data/script.TraktUtilities/"

# Initialise all of the background services
    
def myFunc(x):
    print x
    time.sleep(1)
    print x, "+"
    return x*2
    
def autostart():
        
    #myPool = Pool(10)
    
    #print myPool.nativePool.map(lambda x: x*2, range(20))
    
    # Initialise the cache
    trakt_cache.init(os.path.join(cacheDirectory,"trakt_cache"))
    
    # Initialise the notification handler
    notificationThread = notification_service.NotificationService()
    notificationThread.start()
    
    # Trigger update checks for the cache
    trakt_cache.trigger()
    
    # Wait for the notification handler to quit
    notificationThread.join()
    
autostart()
