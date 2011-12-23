# -*- coding: utf-8 -*-
# 

import xbmc,xbmcaddon,xbmcgui
import telnetlib, time

try: import simplejson as json
except ImportError: import json

import threading
from utilities import *
from rating import *
from sync_update import *
from instant_sync import *
from watchlist import *
from scrobbler import Scrobbler
from viewer import Viewer

__author__ = "Ralph-Gordon Paul, Adrian Cowan"
__credits__ = ["Ralph-Gordon Paul", "Adrian Cowan", "Justin Nemeth",  "Sean Rudford"]
__license__ = "GPL"
__maintainer__ = "Ralph-Gordon Paul"
__email__ = "ralph-gordon.paul@uni-duesseldorf.de"
__status__ = "Production"

__settings__ = xbmcaddon.Addon( "script.TraktUtilities" )
__language__ = __settings__.getLocalizedString

# Receives XBMC notifications and passes them off to the rating functions
class NotificationService(threading.Thread):
    abortRequested = False
    def run(self):        
        #while xbmc is running
        scrobbler = Scrobbler()
        scrobbler.start()
        
        tn = None
        while (not (self.abortRequested or xbmc.abortRequested)):
            try:
                tn = telnetlib.Telnet('localhost', 9090, 10)
            except IOError as (errno, strerror):
                #connection failed, try again soon
                Debug("[Notification Service] Telnet too soon? ("+str(errno)+") "+strerror)
                time.sleep(1)
                continue
            
            Debug("[Notification Service] Waiting~");
            bCount = 0
            
            while (not (self.abortRequested or xbmc.abortRequested)):
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
                            continue
                        if match == "{":
                            bCount += 1
                        if match == "}":
                            bCount -= 1
                    if bCount > 0:
                        continue
                    if bCount < 0:
                        bCount = 0
                except EOFError:
                    break #go out to the other loop to restart the connection
                
                Debug("[Notification Service] message: " + str(notification))
                
                # Parse recieved notification
                data = json.loads(notification)
                
                # Forward notification to functions
                if 'method' in data and 'params' in data and 'sender' in data['params'] and data['params']['sender'] == 'xbmc':
                    if data['method'] == 'Player.OnStop':
                        scrobbler.playbackEnded()
                    elif data['method'] == 'Player.OnPlay':
                        if 'data' in data['params'] and 'item' in data['params']['data'] and 'id' in data['params']['data']['item'] and 'type' in data['params']['data']['item']:
                            scrobbler.playbackStarted(data['params']['data'])
                    elif data['method'] == 'Player.OnPause':
                        scrobbler.playbackPaused()
                    elif data['method'] in ('VideoLibrary.OnUpdate', 'VideoLibrary.OnRemove'):
                        if 'data' in data['params']:
                            if 'type' in data['params']['data'] and 'id' in data['params']['data']:
                                type = data['params']['data']['type']
                                id = data['params']['data']['id']
                                if type == 'episode':
                                    episode = trakt_cache.getEpisode(localId=id)
                                    if episode is not None:
                                        episode.refresh()
                                    else:
                                        trakt_cache.newLocalEpisode(localId=id)
                                elif type == 'movie':
                                    movie = trakt_cache.getMovie(localId=id)
                                    if movie is not None:
                                        movie.refresh()
                                    else:
                                        trakt_cache.newLocalMovie(localId=id)
                    elif data['method'] == 'System.OnQuit':
                        self.abortRequested = True
                
                if 'method' in data and 'params' in data and 'sender' in data['params'] and data['params']['sender'] == 'TraktUtilities':
                    if data['method'] == 'Other.TraktUtilities.View' and 'data' in data['params']:
                        if 'window' in data['params']['data']:
                            window = data['params']['data']['window']
                            if window == 'watchlistMovies':
                                thread.start_new_thread(Viewer.watchlistMovies, ())
                            elif window == 'watchlistShows':
                                thread.start_new_thread(Viewer.watchlistShows, ())
                            elif window == 'trendingMovies':
                                thread.start_new_thread(Viewer.trendingMovies, ())
                            elif window == 'trendingShows':
                                thread.start_new_thread(Viewer.trendingShows, ())
                            elif window == 'recommendedMovies':
                                thread.start_new_thread(Viewer.recommendedMovies, ())
                            elif window == 'recommendedShows':
                                thread.start_new_thread(Viewer.recommendedShows, ())
                    elif data['method'] == 'Other.TraktUtilities.Sync' and 'data' in data['params']:
                        if 'set' in data['params']['data']:
                            setName = data['params']['data']['set']
                            thread.start_new_thread(trakt_cache.refreshSet, (setName))
                # Trigger update checks for the cache
                #trakt_cache.trigger()
            time.sleep(1)
        if tn is not None: tn.close()
        scrobbler.abortRequested = True