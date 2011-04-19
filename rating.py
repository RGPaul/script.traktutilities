# -*- coding: utf-8 -*-
# 

import os
import xbmc,xbmcaddon,xbmcgui
from utilities import *
  
__author__ = "Ralph-Gordon Paul, Adrian Cowan"
__credits__ = ["Ralph-Gordon Paul", "Adrian Cowan", "Justin Nemeth",  "Sean Rudford"]
__license__ = "GPL"
__maintainer__ = "Ralph-Gordon Paul"
__email__ = "ralph-gordon.paul@uni-duesseldorf.de"
__status__ = "Production"

# read settings
__settings__ = xbmcaddon.Addon( "script.TraktUtilities" )
__language__ = __settings__.getLocalizedString

apikey = '0a698a20b222d0b8637298f6920bf03a'
username = __settings__.getSetting("username")
pwd = sha.new(__settings__.getSetting("password")).hexdigest()
debug = __settings__.getSetting( "debug" )

conn = httplib.HTTPConnection('api.trakt.tv')
headers = {"Content-type": "application/x-www-form-urlencoded", "Accept": "text/plain"}

# ask user if they liked the movie
def doRate(movieid):
    match = xbmcHttpapiQuery(
    "SELECT c09, c00 FROM movie"+
    " WHERE idMovie=%(movieid)d" % {'movieid':movieid})
    
    if match == None:
        #add error message here
        return
    
    imdbid = match[0]
    title = match[1]
    
    # display rate dialog
    import windows
    ui = windows.RateDialog("rate.xml", __settings__.getAddonInfo('path'), "Default")
    ui.initDialog(imdbid)
    ui.doModal()
    del ui
    