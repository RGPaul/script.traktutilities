# -*- coding: utf-8 -*-
# 

import os, sys
import time, socket
import threading
    
__author__ = "Ralph-Gordon Paul, Adrian Cowan"
__credits__ = ["Ralph-Gordon Paul", "Adrian Cowan", "Justin Nemeth",  "Sean Rudford"]
__license__ = "GPL"
__maintainer__ = "Ralph-Gordon Paul"
__email__ = "ralph-gordon.paul@uni-duesseldorf.de"
__status__ = "Production"

class AsyncCloseRequest(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)
    

_Pool__pools = []

# Allows a series of functions to be called async
class Pool():    
    
    def __init__(self, numThreads):
        _Pool__pools.append(self)
        self.slots = numThreads
        self.slotCount = 0
        self.queueCount = 0
        self.event = threading.Condition()
        self.closing = False
    
    def x(self, func, *args, **kwargs):
        return AsyncCall(func, self, *args, **kwargs)
    
    def map(self, func, vals):
        results = []
        for val in vals:
            results.append(self.x(func, val))
        out = []
        for result in results:
            out.append(result.need())
        return out
        
    def join(self):
        self.event.acquire()
        while not self.slotCount < self.slots or self.queueCount <> 0:
            if self.closing:
                raise AsyncCloseRequest('')
            self.event.wait()
        self.event.release()
    
    def finishUp(self):
        self.event.acquire()
        self.closing = True
        self.event.notify()
        self.event.release()
        
    def useSlot(self):
        self.event.acquire()
        self.queueCount +=1
        while self.slotCount >= self.slots:
            self.event.wait()
        self.slotCount += 1
        self.queueCount -= 1
        self.event.notify()
        self.event.release()
        
    def freeSlot(self):
        self.event.acquire()
        self.slotCount -= 1
        self.event.notify()
        self.event.release()
    
class AsyncCall():
    
    def __init__(self, func, pool, *args, **kwargs):
        self.func = func
        self.pool = pool
        self.args = args
        self.kwargs = kwargs
        self.result = None
        self.e = None
        self.returned = False
        self.closing = False
        self.event = threading.Condition()
        if self.pool is not None: pool.useSlot()
        threading.Thread(target=self.__runner).start()
    def __invert__(self):
        self.need()
        
    def __runner(self):
        try:
            r = self.func(*self.args, **self.kwargs)
        except Exception, e:
            import sys
            self.event.acquire()
            self.returned = True
            self.e = sys.exc_info()
            self.event.notify()
            self.event.release()
        else:
            self.event.acquire()
            self.returned = True
            self.result = r
            self.event.notify()
            self.event.release()
        finally:    
            if self.pool is not None: pool.freeSlot()
        
    def need(self):
        self.event.acquire()
        while not self.returned:
            if self.closing:
                raise AsyncCloseRequest('')
            self.event.wait()
        self.event.release()
        if self.e is not None:
            raise self.e[1], None, self.e[2]
        return self.result

def async(func):
    def wrapper(*args, **kwargs):
        if 'pool' in kwargs:
            pool = kwargs['pool']
        else:
            pool = None
        #print globals()
        #globals()[func.__module__].__dict__[func.__name__] = func
        return AsyncCall(func, pool, *args, **kwargs)
    return wrapper