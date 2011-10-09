# -*- coding: utf-8 -*-
# 

import os
import xbmcgui,xbmcaddon,xbmc
from utilities import Debug

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

Debug("default entry point: " + __settings__.getAddonInfo("id") + " - version: " + __settings__.getAddonInfo("version"))

rpccmd = json.dumps({'jsonrpc': '2.0', 'method': 'JSONRPC.NotifyAll','params':{'sender': 'TraktUtilities', 'message': 'TraktUtilities.ShowMenu', 'data':{}}, 'id': 1})
result = xbmc.executeJSONRPC(rpccmd)
result = json.loads(result)
Debug("[Defualt] Menu request result: "+str(result))
