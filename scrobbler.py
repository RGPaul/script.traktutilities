# -*- coding: utf-8 -*-
#

import xbmc
import xbmcaddon
import threading
import time

from utilities import *
from rating import *

__author__ = "Ralph-Gordon Paul, Adrian Cowan"
__credits__ = ["Ralph-Gordon Paul", "Adrian Cowan", "Justin Nemeth",  "Sean Rudford"]
__license__ = "GPL"
__maintainer__ = "Ralph-Gordon Paul"
__email__ = "ralph-gordon.paul@uni-duesseldorf.de"
__status__ = "Production"

# read settings
__settings__ = xbmcaddon.Addon("script.traktutilities")
__language__ = __settings__.getLocalizedString

apikey = '0a698a20b222d0b8637298f6920bf03a'  # scrobbling requires this dev key
username = __settings__.getSetting("username")
pwd = sha.new(__settings__.getSetting("password")).hexdigest()
debug = __settings__.getSetting("debug")

headers = {"Content-type": "application/x-www-form-urlencoded", "Accept": "text/plain"}


class Scrobbler(threading.Thread):
    totalTime = 1
    watchedTime = 0
    startTime = 0
    curVideo = None
    pinging = False
    playlistLength = 1
    abortRequested = False

    def run(self):
        # When requested ping trakt to say that the user is still watching the item
        count = 0
        while (not (self.abortRequested or xbmc.abortRequested)):
            time.sleep(5)  # 1min wait
            #Debug("[Scrobbler] Cycling " + str(self.pinging))
            if self.pinging:
                count += 1
                if count >= 100:
                    Debug("[Scrobbler] Pinging watching " + str(self.curVideo))
                    tmp = time.time()
                    self.watchedTime += tmp - self.startTime
                    self.startTime = tmp
                    self.startedWatching()
                    count = 0
            else:
                count = 0

        Debug("Scrobbler stopping")

    def playbackStarted(self, data):
        self.curVideo = data['item']
        if self.curVideo != None:
            if 'type' in self.curVideo and 'id' in self.curVideo:
                Debug("[Scrobbler] Watching: " + self.curVideo['type'] + " - " + str(self.curVideo['id']))
                try:
                    if not xbmc.Player().isPlayingVideo():
                        Debug("[Scrobbler] Suddenly stopped watching item")
                        return
                    time.sleep(1)  # Wait for possible silent seek (caused by resuming)
                    self.watchedTime = xbmc.Player().getTime()
                    self.totalTime = xbmc.Player().getTotalTime()
                    if self.totalTime == 0:
                        if self.curVideo['type'] == 'movie':
                            self.totalTime = 90
                        elif self.curVideo['type'] == 'episode':
                            self.totalTime = 30
                        else:
                            self.totalTime = 1
                    self.playlistLength = getPlaylistLengthFromXBMCPlayer(data['player']['playerid'])
                    if (self.playlistLength == 0):
                        Debug("[Scrobbler] Warning: Cant find playlist length?!, assuming that this item is by itself")
                        self.playlistLength = 1
                except:
                    Debug("[Scrobbler] Suddenly stopped watching item, or error: " + str(sys.exc_info()[0]))
                    self.curVideo = None
                    self.startTime = 0
                    return
                self.startTime = time.time()
                self.startedWatching()
                self.pinging = True
            else:
                self.curVideo = None
                self.startTime = 0

    def playbackPaused(self):
        if self.startTime != 0:
            self.watchedTime += time.time() - self.startTime
            Debug("[Scrobbler] Paused after: " + str(self.watchedTime))
            self.startTime = 0

    def playbackEnded(self):
        if self.startTime != 0:
            if self.curVideo == None:
                Debug("[Scrobbler] Warning: Playback ended but video forgotten")
                return
            self.watchedTime += time.time() - self.startTime
            self.pinging = False
            if self.watchedTime != 0:
                if 'type' in self.curVideo and 'id' in self.curVideo:
                    self.check()
                    ratingCheck(self.curVideo, self.watchedTime, self.totalTime, self.playlistLength)
                self.watchedTime = 0
            self.startTime = 0

    def startedWatching(self):
        scrobbleMovieOption = __settings__.getSetting("scrobble_movie")
        scrobbleEpisodeOption = __settings__.getSetting("scrobble_episode")

        if self.curVideo['type'] == 'movie' and scrobbleMovieOption == 'true':
            match = getMovieDetailsFromXbmc(self.curVideo['id'], ['imdbnumber', 'title', 'year'])
            if match == None:
                return
            responce = watchingMovieOnTrakt(match['imdbnumber'], match['title'], match['year'], self.totalTime / 60, int(100 * self.watchedTime / self.totalTime))
            if responce != None:
                Debug("[Scrobbler] Watch responce: " + str(responce))
        elif self.curVideo['type'] == 'episode' and scrobbleEpisodeOption == 'true':
            match = getEpisodeDetailsFromXbmc(self.curVideo['id'], ['showtitle', 'season', 'episode'])
            if match == None:
                return
            responce = watchingEpisodeOnTrakt(None, match['showtitle'], None, match['season'], match['episode'], self.totalTime / 60, int(100 * self.watchedTime / self.totalTime))
            if responce != None:
                Debug("[Scrobbler] Watch responce: " + str(responce))

    def stoppedWatching(self):
        scrobbleMovieOption = __settings__.getSetting("scrobble_movie")
        scrobbleEpisodeOption = __settings__.getSetting("scrobble_episode")

        if self.curVideo['type'] == 'movie' and scrobbleMovieOption == 'true':
            responce = cancelWatchingMovieOnTrakt()
            if responce != None:
                Debug("[Scrobbler] Cancel watch responce: " + str(responce))
        elif self.curVideo['type'] == 'episode' and scrobbleEpisodeOption == 'true':
            responce = cancelWatchingEpisodeOnTrakt()
            if responce != None:
                Debug("[Scrobbler] Cancel watch responce: " + str(responce))

    def scrobble(self):
        scrobbleMovieOption = __settings__.getSetting("scrobble_movie")
        scrobbleEpisodeOption = __settings__.getSetting("scrobble_episode")

        if self.curVideo['type'] == 'movie' and scrobbleMovieOption == 'true':
            match = getMovieDetailsFromXbmc(self.curVideo['id'], ['imdbnumber', 'title', 'year'])
            if match == None:
                return
            responce = scrobbleMovieOnTrakt(match['imdbnumber'], match['title'], match['year'], self.totalTime / 60, int(100 * self.watchedTime / self.totalTime))
            if responce != None:
                Debug("[Scrobbler] Scrobble responce: " + str(responce))
        elif self.curVideo['type'] == 'episode' and scrobbleEpisodeOption == 'true':
            match = getEpisodeDetailsFromXbmc(self.curVideo['id'], ['showtitle', 'season', 'episode'])
            if match == None:
                return
            responce = scrobbleEpisodeOnTrakt(None, match['showtitle'], None, match['season'], match['episode'], self.totalTime / 60, int(100 * self.watchedTime / self.totalTime))
            if responce != None:
                Debug("[Scrobbler] Scrobble responce: " + str(responce))

    def check(self):
        __settings__ = xbmcaddon.Addon("script.traktutilities")  # read settings again, encase they have changed
        scrobbleMinViewTimeOption = __settings__.getSetting("scrobble_min_view_time")

        if (self.watchedTime / self.totalTime) * 100 >= float(scrobbleMinViewTimeOption):
            self.scrobble()
        else:
            self.stoppedWatching()
