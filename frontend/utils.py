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
from xml.dom import minidom
import config

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
        self.ser.port = config.ser_port
        self.ser.open()

    def run(self):
        """
        Read serial until thread killed
        """
        while self.isOk==True:
            self.scale_string=self.ser.readline()

    def isStable(self):
        "Return true iff the weight on the scale is stable"
        return self.pattern_matcher.findall(self.scale_string)[0][0]=="ST"

    def getWeight(self):
        "Returns the value of the weight on the scale as float"
        return float(self.pattern_matcher.findall(self.scale_string)[0][2])

    def kill(self):
        """Called when thread must be killed. Causes loop of thread to 
        terminate and thread to die"""
        self.isOk=False

class DBAPI ():
    def __init__(self):
        self.http_address = config.django_http_path

    def addBox(self,picker,batch,variety,initWeight,finalWeight,timestamp): 
        """ Performs a url request with for the django add box using all the
        info in parameters
            
                Returns (p,m) p is true iff the operation was successful
                else m is the error message returned from the server
        """
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
        """ 
            Parse a delimited string from a url of all the current pickers
            into a python list
        """
        l=list()
        f=urllib.urlopen(self.http_address+"pickerList")
        for p in f.read().split("*")[:-1]:
            l.append(p.split("|"))
        return l        

    def getActivePickersXML(self):
        """ 
            Parse an xml list of all the current pickers into a python list
        """
        l=list()
        xmldoc = minidom.parse(urllib.urlopen(self.http_address+"pickerList.xml"))
        for picker in xmldoc.getElementsByTagName("picker"):
            l.append([picker.getElementsByTagName("id")[0].firstChild.data,
              picker.getElementsByTagName("firstName")[0].firstChild.data,
              picker.getElementsByTagName("lastName")[0].firstChild.data])
        return l
            
    def getActiveBatches(self):    
        """ 
            Parse a delimited string from a url of all the current batches into
            a python list
        """
        l=list()
        f=urllib.urlopen(self.http_address+"batchList")
        for p in f.read().split("*")[:-1]:
            l.append(p.split("|"))
        return l        

    def getActiveBatchesXML(self):
        """ 
            Parse an xml list of all the current batches into a python list
        """
        l=list()
        xmldoc = minidom.parse(urllib.urlopen(self.http_address+"batchList.xml"))
        for batch in xmldoc.getElementsByTagName("batch"):
            id=batch.getElementsByTagName("id")[0].firstChild.data
            monthstring=batch.getElementsByTagName("date")[0].getElementsByTagName("day")[0].firstChild.data
            monthstring+="/"+batch.getElementsByTagName("date")[0].getElementsByTagName("month")[0].firstChild.data
            monthstring+="/"+batch.getElementsByTagName("date")[0].getElementsByTagName("year")[0].firstChild.data
            roomnumber=batch.getElementsByTagName("room")[0].getElementsByTagName("number")[0].firstChild.data
            l.append([id,monthstring,roomnumber])
        return l
     
    def getActiveVarieties(self):    
        """ 
            Parse a delimited string from a url of all the current batches into
            a python list
        """
        l=list()
        f=urllib.urlopen(self.http_address+"varietyList")
        for p in f.read().split("*")[:-1]:
        # Last elements are the idealWeight and Tolerance
            #l.append(p.split("|")[:-2])
            l.append(p.split("|"))
        return l        

    def getActiveVarietiesXML(self):
        """ Parse an xml list of all varieties into a python list
            NOTE: as of 11/2/2011 the list now performs the cast to float
                    for the number values
        """
        l=list()
        xmldoc = minidom.parse(urllib.urlopen(self.http_address+"varietyList.xml"))
        for varieties in xmldoc.getElementsByTagName("variety"):
            l.append([varieties.getElementsByTagName("id")[0].firstChild.data,
              varieties.getElementsByTagName("name")[0].firstChild.data,
              float(varieties.getElementsByTagName("idealWeight")[0].firstChild.data),
              float(varieties.getElementsByTagName("tolerance")[0].firstChild.data)])
        return l
     
