# -*- coding: utf-8 -*-
# 

import os, sys
import time, socket
import urllib
import threading

try:
    # Python 3.0 +
    import http.client as httplib
except ImportError:
    # Python 2.7 and earlier
    import httplib

try:
  # Python 2.6 +
  from hashlib import sha as sha
except ImportError:
  # Python 2.5 and earlier
  import sha
  
__author__ = "Ralph-Gordon Paul, Adrian Cowan"
__credits__ = ["Ralph-Gordon Paul", "Adrian Cowan", "Justin Nemeth",  "Sean Rudford"]
__license__ = "GPL"
__maintainer__ = "Ralph-Gordon Paul"
__email__ = "ralph-gordon.paul@uni-duesseldorf.de"
__status__ = "Production"

# Allows non-blocking http requests
class NBHTTPConnection(threading.Thread):    
    def __init__(self, host, port = None, strict = None, timeout = None):
        self.rawConnection = httplib.HTTPConnection(host, port, strict, timeout)
        self.responce = None
        self.responceLock = threading.Lock()
        self.closing = False
        
        threading.Thread.__init__(self)
    
    def request(self, method, url, body = None, headers = {}):
        self.rawConnection.request(method, url, body, headers);
    
    def hasResult(self):
        if self.responceLock.acquire(False):
            self.responceLock.release()
            return True
        else:
            return False
        
    def getResult(self):
        while not self.hasResult() and not self.closing:
            time.sleep(1)
        return self.responce
    
    def go(self):
        self.responceLock.acquire()
        print str(self.responceLock)
        self.start()
        
    def run(self):
        self.responce = self.rawConnection.getresponse()
        self.responceLock.release()
        
    def close(self):
        self.closing = True
        self.rawConnection.close()
    