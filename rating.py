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

headers = {"Content-type": "application/x-www-form-urlencoded", "Accept": "text/plain"}

totalTime = 0
watchedTime = 0
startTime = 0
curVideo = None

# ask user if they liked the movie
def doRateMovie(movieid=None, imdbid=None, title=None, year=None):
    if (movieid <> None) :
        match = xbmcHttpapiQuery(
        "SELECT c09, c00, c07 FROM movie"+
        " WHERE idMovie=%(movieid)d" % {'movieid':movieid})
        
        if not match:
            #add error message here
            return
        
        imdbid = match[0]
        title = match[1]
        year = match[2]
        
    # display rate dialog
    import windows
    ui = windows.RateMovieDialog("rate.xml", __settings__.getAddonInfo('path'), "Default")
    ui.initDialog(imdbid, title, year, getMovieRatingFromTrakt(imdbid, title, year))
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
    
    if not match:
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
    ui.initDialog(tvdbid, title, year, season, episode, getEpisodeRatingFromTrakt(tvdbid, title, year, season, episode))
    ui.doModal()
    del ui
    
def ratingPlaybackStarted():
    global startTime
    global totalTime
    global curVideo
    
    Debug("[~]"+str(totalTime))
    if xbmc.Player().isPlayingVideo():
        curVideo = getCurrentPlayingVideoFromXBMC()
        if curVideo <> None:
            if 'type' in curVideo and 'id' in curVideo: Debug("[Rating] Watching: "+curVideo['type']+" - "+str(curVideo['id']))
            totalTime = xbmc.Player().getTotalTime()
            startTime = time.time()

def ratingPlaybackPaused():
    global startTime
    global watchedTime
    
    if startTime <> 0:
        watchedTime += time.time() - startTime
        Debug("[Rating] Paused after: "+str(watchedTime))
        startTime = 0

def ratingPlaybackEnded():
    global startTime
    global watchedTime
    global totalTime
    global curVideo

    # you can disable rating in options
    __settings__ = xbmcaddon.Addon( "script.TraktUtilities" ) #read settings again, encase they have changed
    rateMovieOption = __settings__.getSetting("rate_movie")
    rateEpisodeOption = __settings__.getSetting("rate_episode")
    rateEachInPlaylistOption = __settings__.getSetting("rate_each_playlist_item")
    rateMinViewTimeOption = __settings__.getSetting("rate_min_view_time")
    
    if startTime <> 0:
        watchedTime += time.time() - startTime
        if watchedTime <> 0:
            Debug("[Rating] Time watched: "+str(watchedTime)+", Item length: "+str(totalTime))     
            if 'type' in curVideo and 'id' in curVideo:
                if (watchedTime/totalTime)*100>=float(rateMinViewTimeOption):
                    if (getCurrentPlaylistLengthFromXBMC() <= 1) or (rateEachInPlaylistOption == 'true'):
                        if curVideo['type'] == 'movie' and rateMovieOption == 'true':
                            doRateMovie(curVideo['id'])
                        if curVideo['type'] == 'episode' and rateEpisodeOption == 'true':
                            doRateEpisode(curVideo['id'])
            watchedTime = 0
        startTime = 0
