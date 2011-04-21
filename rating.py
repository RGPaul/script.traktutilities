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
def doRateMovie(movieid):
    match = xbmcHttpapiQuery(
    "SELECT c09, c00, c07 FROM movie"+
    " WHERE idMovie=%(movieid)d" % {'movieid':movieid})
    
    if match == None:
        #add error message here
        return
    
    imdbid = match[0]
    title = match[1]
    year = match[2]
    
    # display rate dialog
    import windows
    ui = windows.RateMovieDialog("rate.xml", __settings__.getAddonInfo('path'), "Default")
    ui.initDialog(imdbid, title, year)
    ui.doModal()
    del ui

# ask user if they liked the movie
def doRateEpisode(episodeid):
    match = xbmcHttpapiQuery(
    "SELECT tvshow.c12, tvshow.c00, tvshow.c05, episode.c12, episode.c13 FROM tvshow"+
    " INNER JOIN tvshowlinkepisode"+
    " ON tvshow.idShow = tvshowlinkepisode.idShow"+
    " INNER JOIN episode"+
    " ON tvshowlinkepisode.idEpisode = episode.idEpisode"+
    " WHERE episode.idEpisode=%(episodeid)d" % {'episodeid':episodeid})
    
    if match == None:
        #add error message here
        return
    
    tvdbid = match[0]
    title = match[1]
    year = match[2]
    season = match[3]
    episode = match[4]
    
    # display rate dialog
    import windows
    ui = windows.RateEpisodeDialog("rate.xml", __settings__.getAddonInfo('path'), "Default")
    ui.initDialog(tvdbid, title, year, season, episode)
    ui.doModal()
    del ui