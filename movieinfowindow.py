# -*- coding: utf-8 -*-
# @author Ralph-Gordon Paul
# 

import xbmc,xbmcaddon,xbmcgui
from utilities import *

__settings__ = xbmcaddon.Addon( "script.TraktUtilities" )
__language__ = __settings__.getLocalizedString

MOVIE_TITLE = 3

class MovieInfoWindow(xbmcgui.WindowXMLDialog):

    movieTitle = ""

    def __init__(self, *args, **kwargs):
        pass
    
    def onInit( self ):
        self.getControl(MOVIE_TITLE).setLabel(self.movieTitle)

    def onClick( self, controlId ):
    	pass
        
    def onFocus( self, controlId ):
    	self.controlId = controlId
    
    def setTitle(self, title):
        self.movieTitle = title

def onAction( self, action ):
    if ( action.getButtonCode() in CANCEL_DIALOG ):
        Debug("Closing MovieInfoWindow")
        self.close()
