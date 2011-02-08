#!/usr/bin/python

import serial
import threading
import urllib
from datetime import datetime
from os import system
#import pyaudio
import wave
import sys
from multiprocessing import Process

chunk = 1024

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
    def __init__(self):
        threading.Thread.__init__(self)
        self.isOk=True
        self.weight="ST,GS, 0.0KG,"
        self.ser=serial.Serial()
        self.ser.port=ser_port
        self.ser.open()

    def run(self):
        while self.isOk==True:
            self.weight=self.ser.readline()

    def isStable(self):
        return self.weight[0:2]=="ST"

    def getWeight(self):
        return float(self.weight[6]+self.weight.split()[1][:-3])

    def kill(self):
        self.isOk=False

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

#class SoundPlayerOld(Process):
#    def __init__(self):
#        #threading.Thread.__init__(self)
#        Process.__init__(self)
#        self.isOk=True
#        self.playSound=False
#
#    def run(self):
#        while self.isOk==True:
#            if self.playSound==True:
#                print"wtf"
#	        system("aplay Front_Center.wav")
#                self.playSound=False
#            print self.playSound
#
#    def play(self):
#        print self.playSound
#        self.playSound=True
#        print self.playSound
#
#    def kill(self):
#        self.isOk=False
#
#
#class SoundPlayer(threading.Thread):
#    def __init__(self, fname):
#        threading.Thread.__init__(self)
#        self.p = pyaudio.PyAudio()
#        self.chunk = 1024
#        self.wf = wave.open(fname, 'rb')
#        self.isOk=True
#
#    def run(self):
#        while self.isOk==True:
#            pass
#
#    def play(self):
## open stream
#        self.stream = self.p.open(format =
#                self.p.get_format_from_width(self.wf.getsampwidth()),
#                channels = self.wf.getnchannels(),
#                rate = self.wf.getframerate(),
#                output = True)
## read data
#        self.data = self.wf.readframes(chunk)
#        # play stream
#        while self.data != '':
#            self.stream.write(self.data)
#            self.data = self.wf.readframes(self.chunk)
#        self.stream.close()
#        self.p.terminate()
#
#    def kill(self):
#        self.isOk=False
#


