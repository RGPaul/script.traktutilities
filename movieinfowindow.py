# -*- coding: utf-8 -*-
# @author Ralph-Gordon Paul
# 

import xbmc,xbmcaddon,xbmcgui
from utilities import *

__settings__ = xbmcaddon.Addon( "script.TraktUtilities" )
__language__ = __settings__.getLocalizedString

MOVIE_TITLE = 3
MOVIE_OVERVIEW = 4
MOVIE_POSTER = 5

class MovieInfoWindow(xbmcgui.WindowXMLDialog):

    title = ""
    overview = ""

    def __init__(self, *args, **kwargs):
        pass
    
    def onInit( self ):
        self.getControl(MOVIE_TITLE).setLabel(self.title)
        self.getControl(MOVIE_OVERVIEW).setLabel(self.overview)
        self.getControl(MOVIE_POSTER).setImage(os.getcwd() + os.sep + "data" + os.sep + "poster.jpg")

    def onClick( self, controlId ):
    	pass
        
    def onFocus( self, controlId ):
    	self.controlId = controlId
    
    def setTitle(self, title):
        self.title = title
        
    def setOverview(self, overview):
        self.overview = overview
    
    def setCover(self, cover):
        self.cover = cover

def onAction( self, action ):
    if ( action.getButtonCode() in CANCEL_DIALOG ):
        Debug("Closing MovieInfoWindow")
        self.close()
