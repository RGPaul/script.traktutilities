# -*- coding: utf-8 -*-
# 

import xbmc,xbmcaddon,xbmcgui
import telnetlib, time
import simplejson as json
import threading
from utilities import *
from rating import *
from sync_update import *

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
        ratingThread = RatingService()
        ratingThread.start()
        
        autosync_moviecollection = __settings__.getSetting("autosync_moviecollection")
        autosync_tvshowcollection = __settings__.getSetting("autosync_tvshowcollection")
        autosync_seenmovies = __settings__.getSetting("autosync_seenmovies")
        autosync_seentvshows = __settings__.getSetting("autosync_seentvshows")
        
        if autosync_moviecollection == "true":
            notification("Trakt Utilities", __language__(1180).encode( "utf-8", "ignore" )) # start movie collection update
            updateMovieCollection(True)
        if autosync_tvshowcollection == "true":
            notification("Trakt Utilities", __language__(1181).encode( "utf-8", "ignore" )) # start tvshow collection update
            updateTVShowCollection(True)
        if autosync_seenmovies == "true":
            Debug("autostart sync seen movies")
            notification("Trakt Utilities", __language__(1182).encode( "utf-8", "ignore" )) # start sync seen movies
            syncSeenMovies(True)
        if autosync_seentvshows == "true":
            Debug("autostart sync seen tvshows")
            notification("Trakt Utilities", __language__(1183).encode( "utf-8", "ignore" )) # start sync seen tv shows
            syncSeenTVShows(True)
            
        if autosync_moviecollection == "true" or autosync_tvshowcollection == "true" or autosync_seenmovies == "true" or autosync_seentvshows == "true":
            notification("Trakt Utilities", __language__(1184).encode( "utf-8", "ignore" )) # update / sync done
        
        ratingThread.join()

class RatingService(threading.Thread):
    def run(self):
        #initial state
        self.totalTime = 0
        self.watchedTime = 0
        self.startTime = 0
        self.curVideo = None
        
        #while xbmc is running
        while (not xbmc.abortRequested):
            try:
                tn = telnetlib.Telnet('localhost', 9090, 10)
            except IOError as (errno, strerror):
                #connection failed, try again soon
                Debug("[Rating] Telnet too soon? ("+str(errno)+") "+strerror)
                time.sleep(1)
                continue
            
            Debug("[Rating] Waiting");
            bCount = 0
            
            while (not xbmc.abortRequested):
                try:
                    if bCount == 0:
                        notification = ""
                        inString = False
                    [index, match, raw] = tn.expect(["(\\\\)|(\\\")|[{\"}]"], 0.2) #note, pre-compiled regex might be faster here
                    notification += raw
                    if index == -1: # Timeout
                        continue
                    if index == 0: # Found escaped quote
                        match = match.group(0)
                        if match == "\"":
                            inString = not inString
                            #Debug("[~] "+match+" "+str(inString)+" >"+raw)
                            continue
                        if match == "{":
                            bCount += 1
                            #Debug("[~] "+match+" "+str(bCount)+" >"+raw)
                        if match == "}":
                            bCount -= 1
                            #Debug("[~] "+match+" "+str(bCount)+" >"+raw)
                    if bCount > 0:
                        continue
                    if bCount < 0:
                        bCount = 0
                except EOFError:
                    break #go out to the other loop to restart the connection
                
                #Debug("[Rating] message: " + str(notification))
                data = json.loads(notification)
                __settings__ = xbmcaddon.Addon( "script.TraktUtilities" ) #read settings again, encase they have changed
                # you can disable rating in options
                rateMovieOption = __settings__.getSetting("rate_movie")
                rateEpisodeOption = __settings__.getSetting("rate_episode")
                rateEachInPlaylistOption = __settings__.getSetting("rate_each_playlist_item")
                rateMinViewTimeOption = __settings__.getSetting("rate_min_view_time")
                if 'method' in data and 'params' in data and 'sender' in data['params'] and data['params']['sender'] == 'xbmc':
                    if data['method'] in ('Player.PlaybackStopped', 'Player.PlaybackEnded'):
                        if self.startTime <> 0:
                            self.watchedTime += time.time() - self.startTime
                            if self.watchedTime <> 0:
                                Debug("[Rating] Time watched: "+str(self.watchedTime)+", Item length: "+str(self.totalTime))     
                                if 'type' in self.curVideo and 'id' in self.curVideo:
                                    if (self.watchedTime/self.totalTime)*100>=float(rateMinViewTimeOption):
                                        if (getCurrentPlaylistLengthFromXBMC() <= 1) or (rateEachInPlaylistOption == 'true'):
                                            if self.curVideo['type'] == 'movie' and rateMovieOption == 'true':
                                                doRateMovie(self.curVideo['id'])
                                            if self.curVideo['type'] == 'episode' and rateEpisodeOption == 'true':
                                                doRateEpisode(self.curVideo['id'])
                                self.watchedTime = 0
                            self.startTime = 0
                    elif data['method'] in ('Player.PlaybackStarted', 'Player.PlaybackResumed'):
                        if xbmc.Player().isPlayingVideo():
                            self.curVideo = getCurrentPlayingVideoFromXBMC()
                            if self.curVideo <> None:
                                if 'type' in self.curVideo and 'id' in self.curVideo: Debug("[Rating] Watching: "+self.curVideo['type']+" - "+str(self.curVideo['id']))
                                self.totalTime = xbmc.Player().getTotalTime()
                                self.startTime = time.time()
                    elif data['method'] == 'Player.PlaybackPaused':
                        if self.startTime <> 0:
                            self.watchedTime += time.time() - self.startTime
                            Debug("[Rating] Paused after: "+str(self.watchedTime))
                            self.startTime = 0
            time.sleep(1)

autostart()
