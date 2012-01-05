# -*- coding: utf-8 -*-
# 

import shelve
from threading import Lock, Semaphore
from utilities import Debug
import traceback

__author__ = "Ralph-Gordon Paul, Adrian Cowan"
__credits__ = ["Ralph-Gordon Paul", "Adrian Cowan", "Justin Nemeth",  "Sean Rudford"]
__license__ = "GPL"
__maintainer__ = "Ralph-Gordon Paul"
__email__ = "ralph-gordon.paul@uni-duesseldorf.de"
__status__ = "Production"

class SafeShelf:
    __writeMutex = {}
    __readMutex = {}
    __readCount = {}
    __shelf = {}
    
    def __init__(self, name, writeable = False):
        self.name = name
        self.writeable = writeable
        #+" from "+repr(traceback.format_stack()))
        
    @staticmethod
    def set(name, shelf):
        SafeShelf.__shelf[name] = shelf
        SafeShelf.__writeMutex[name] = Lock()
        SafeShelf.__readMutex[name] = Lock()
        SafeShelf.__readCount[name] = 0
    
    def __enter__(self):
        #Debug("[~] Requested "+str(self.name)+","+str(self.writeable))
        if self.writeable:
            if self.name not in SafeShelf.__shelf:
                SafeShelf.__shelf[self.name] = None
                SafeShelf.__writeMutex[self.name] = Lock()
                SafeShelf.__readMutex[self.name] = Lock()
                SafeShelf.__readCount[self.name] = 0
            with SafeShelf.__readMutex[self.name]:
                SafeShelf.__writeMutex[self.name].acquire()
            return SafeShelf.__shelf[self.name]
        else:
            if self.name not in SafeShelf.__shelf:
                raise NameError("Shelf "+repr(self.name)+" is not defined")
            with SafeShelf.__writeMutex[self.name]:
                if SafeShelf.__readCount[self.name] == 0:
                    SafeShelf.__readMutex[self.name].acquire()
                SafeShelf.__readCount[self.name] += 1
            return SafeShelf.__shelf[self.name]
        
    def __exit__(self, type, value, traceback):
        if self.writeable:
            with SafeShelf.__readMutex[self.name]:
                SafeShelf.__writeMutex[self.name].release()
        else:
            with SafeShelf.__writeMutex[self.name]:
                SafeShelf.__readCount[self.name] -= 1
                if SafeShelf.__readCount[self.name] == 0:
                    SafeShelf.__readMutex[self.name].release()
        #Debug("[~] released "+str(self.name)+","+str(self.writeable))