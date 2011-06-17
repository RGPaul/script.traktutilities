# -*- coding: utf-8 -*-
# 

import os
import xbmc,xbmcaddon,xbmcgui
import threading
from utilities import *
from rating import *
  
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

class Scrobbler(threading.Thread):
    totalTime = 0
    watchedTime = 0
    startTime = 0
    curVideo = None
    pinging = False
    
    def run(self):
        # When requested ping trakt to say that the user is still watching the item
        count = 0
        while (not xbmc.abortRequested):
            time.sleep(60) # 1min wait
            Debug("[Scrobbler] Cycling " + str(self.pinging))
            if self.pinging:
                count += 1
                if count>=10:
                    Debug("[Scrobbler] Pinging watching "+str(self.curVideo))
                    tmp = time.time()
                    self.watchedTime += tmp - self.startTime
                    self.startTime = tmp
                    self.startedWatching()
                    count = 0
            else:
                count = 0
    
    def playbackStarted(self):
        if xbmc.Player().isPlayingVideo():
            self.curVideo = getCurrentPlayingVideoFromXBMC()
            if self.curVideo <> None:
                if 'type' in self.curVideo and 'id' in self.curVideo:
                    Debug("[Rating] Watching: "+self.curVideo['type']+" - "+str(self.curVideo['id']))
                    self.totalTime = xbmc.Player().getTotalTime()
                    self.startTime = time.time()
                    self.startedWatching()
                    self.pinging = True
                else:
                    self.curVideo = None

    def playbackPaused(self):
        if self.startTime <> 0:
            self.watchedTime += time.time() - self.startTime
            Debug("[Rating] Paused after: "+str(self.watchedTime))
            self.startTime = 0
            self.pinging = False
            self.stoppedWatching()

    def playbackEnded(self):
        if self.startTime <> 0:
            self.watchedTime += time.time() - self.startTime
            self.pinging = False
            if self.watchedTime <> 0:
                if 'type' in self.curVideo and 'id' in self.curVideo:
                    self.check()
                    ratingCheck(self.curVideo, self.watchedTime, self.totalTime)
                self.watchedTime = 0
            self.startTime = 0
            
    def startedWatching(self):
        scrobbleMovieOption = __settings__.getSetting("scrobble_movie")
        scrobbleEpisodeOption = __settings__.getSetting("scrobble_episode")
        
        if self.curVideo['type'] == 'movie' and scrobbleMovieOption == 'true':
            match = getMovieDetailsFromXbmc(self.curVideo['id'], ['imdbnumber','title','year'])
            if match == None:
                return
            responce = watchingMovieOnTrakt(match['imdbnumber'], match['title'], match['year'], self.totalTime/60, int(100*self.watchedTime/self.totalTime))
            if responce != None:
                Debug("[Scrobbler] Watch responce: "+str(responce));
        elif self.curVideo['type'] == 'episode' and scrobbleEpisodeOption == 'true':
            match = getEpisodeDetailsFromXbmc(self.curVideo['id'], ['showtitle', 'season', 'episode'])
            if match == None:
                return
            responce = watchingEpisodeOnTrakt(None, match['showtitle'], None, match['season'], match['episode'], self.totalTime/60, int(100*self.watchedTime/self.totalTime))
            if responce != None:
                Debug("[Scrobbler] Watch responce: "+str(responce));
        
    def stoppedWatching(self):
        scrobbleMovieOption = __settings__.getSetting("scrobble_movie")
        scrobbleEpisodeOption = __settings__.getSetting("scrobble_episode")
        
        if self.curVideo['type'] == 'movie' and scrobbleMovieOption == 'true':
            responce = cancelWatchingMovieOnTrakt()
            if responce != None:
                Debug("[Scrobbler] Cancel watch responce: "+str(responce));
        elif self.curVideo['type'] == 'episode' and scrobbleEpisodeOption == 'true':
            responce = cancelWatchingEpisodeOnTrakt()
            if responce != None:
                Debug("[Scrobbler] Cancel watch responce: "+str(responce));
            
    def scrobble(self):
        scrobbleMovieOption = __settings__.getSetting("scrobble_movie")
        scrobbleEpisodeOption = __settings__.getSetting("scrobble_episode")
        
        if self.curVideo['type'] == 'movie' and scrobbleMovieOption == 'true':
            match = getMovieDetailsFromXbmc(self.curVideo['id'], ['imdbnumber','title','year'])
            if match == None:
                return
            responce = scrobbleMovieOnTrakt(match['imdbnumber'], match['title'], match['year'], self.totalTime/60, int(100*self.watchedTime/self.totalTime))
            if responce != None:
                Debug("[Scrobbler] Scrobble responce: "+str(responce));
        elif self.curVideo['type'] == 'episode' and scrobbleEpisodeOption == 'true':
            match = getEpisodeDetailsFromXbmc(self.curVideo['id'], ['showtitle', 'season', 'episode'])
            if match == None:
                return
            responce = scrobbleEpisodeOnTrakt(None, match['showtitle'], None, match['season'], match['episode'], self.totalTime/60, int(100*self.watchedTime/self.totalTime))
            if responce != None:
                Debug("[Scrobbler] Scrobble responce: "+str(responce));

    def check(self):
        __settings__ = xbmcaddon.Addon( "script.TraktUtilities" ) #read settings again, encase they have changed
        scrobbleMinViewTimeOption = __settings__.getSetting("scrobble_min_view_time")
        
        if (self.watchedTime/self.totalTime)*100>=float(scrobbleMinViewTimeOption):
            self.scrobble()
        else:
            self.stoppedWatching()
