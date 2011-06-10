# -*- coding: utf-8 -*-
# 

import xbmc,xbmcaddon,xbmcgui
import telnetlib, time
import simplejson as json
import threading
from utilities import *
from rating import *
from sync_update import *
from instant_sync import *

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
    def run(self):        
        #while xbmc is running
        while (not xbmc.abortRequested):
            try:
                tn = telnetlib.Telnet('localhost', 9090, 10)
            except IOError as (errno, strerror):
                #connection failed, try again soon
                Debug("[Rating] Telnet too soon? ("+str(errno)+") "+strerror)
                time.sleep(1)
                continue
            
            Debug("[Rating] Waiting~");
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
                
                Debug("[Rating] message: " + str(notification))
                
                # Parse recieved notification
                data = json.loads(notification)
                
                # Forward notification to functions
                if 'method' in data and 'params' in data and 'sender' in data['params'] and data['params']['sender'] == 'xbmc':
                    if data['method'] == 'Player.OnStop':
                        ratingPlaybackEnded()
                    elif data['method'] == 'Player.OnPlay':
                        ratingPlaybackStarted()
                    elif data['method'] == 'Player.OnPause':
                        ratingPlaybackPaused()
                    elif data['method'] == 'VideoLibrary.OnUpdate':
                        if 'data' in data['params'] and 'playcount' in data['params']['data']:
                            instantSyncPlayCount(data)
                
            time.sleep(1)