#!/usr/bin/python

"""
This is a library of classes for use within the Gleba Software system

Copyright (C) Simon Dawson, Kenji Toyama, Meryl Baquiran, Chris Ellis 2010-2011
"""

import serial
import threading
import urllib
from datetime import datetime
import re

#==========================================
#   Don't edit above this line.
#   CONFIGS
#
# - Serial Configuration
ser_port=1#"/dev/ttyS0"

# - Django Configuration
#    Full http path to the root of the django web app 
#         Change before deployment
django_http_path="http://hellscream.hayday.biz/gleba"

#    Don't edit below this line
#==========================================

class ThreadSerial(threading.Thread):
    """
    Opens a serial connection on the port specified in the glocal variable section

    Starts a thread which reads from it. It will return the value of the weight as
    the getWeight method is called.

    As of 9/2/11 this is untested using a serial scale.
    """
    def __init__(self):
        """
        Open a start a new thread which will read from the serial port opened
        in this function.
        """
        threading.Thread.__init__(self)
        self.isOk=True
        self.pattern_matcher=re.compile(r"^(ST|US),(GS|[A-Z]+), (\d+\.\d+)KG,$")
        self.scale_string="ST,GS, 0.0KG,"
        self.ser=serial.Serial()
        self.ser.port=ser_port
        self.ser.open()

    def run(self):
        """
        Read serial until thread killed
        """
        while self.isOk==True:
            self.weight_string=self.ser.readline()

    def isStable(self):
        "Return true iff the weight on the scale is stable"
        return self.pattern_matcher.findall(self.scale_string)[0][0]=="ST"

    def getWeight(self):
        "Returns the value of the weight on the scale as float"
        return float(self.pattern_matcher.findall(self.scale_string)[0][2])

    def kill(self):
        " Called when thread must be killed. Causes loop of thread to terminate and thread to die"
        self.isOk=False

""" TODO: Re-write to use XML Parser """

class DBAPI ():
    def __init__(self):
        self.http_address=django_http_path

    def addBox (self,picker, batch, variety, initWeight, finalWeight, timestamp):    
        params=urllib.urlencode({
            'initialWeight':initWeight,
            'finalWeight':finalWeight,
            'timestamp':timestamp,
            'contentVariety':variety,
            'picker':picker,
            'batch':batch
            })
        f=urllib.urlopen((self.http_address+"addBox?%s")%params)
        r=((f.read()=="success"),f.read())
        return r
        
    def getActivePickers(self):    
        l=list()
        f=urllib.urlopen(self.http_address+"pickerList")
        for p in f.read().split("*")[:-1]:
            l.append(p.split("|"))
        return l        

    def getActiveBatches(self):    
        l=list()
        f=urllib.urlopen(self.http_address+"batchList")
        for p in f.read().split("*")[:-1]:
            l.append(p.split("|"))
        return l        

    def getActiveVarieties(self):    
        l=list()
        f=urllib.urlopen(self.http_address+"varietyList")
        for p in f.read().split("*")[:-1]:
        # Last elements are the idealWeight and Tolerance
            #l.append(p.split("|")[:-2])
            l.append(p.split("|"))
        return l        

