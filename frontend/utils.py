#!/usr/bin/python

"""
This is a library of classes for use within the Gleba Software system

Copyright (C) Simon Dawson, Kenji Toyama, Meryl Baquiran, Chris Ellis
2010-2011
"""

import serial
import threading
import urllib
import re
from xml.dom import minidom
import config
from json import dumps, loads

class ThreadSerial(threading.Thread):
    """
    Opens a serial connection on the port specified in config.py.

    Starts a thread which consumes the serial port and returns the value of
    the weight as the get_weight method is called.

    As of 9/2/11 this is untested using a serial scale (just the simulator).
    """
    def __init__(self):
        """
        Sets up the running environment for reading the serial port.
        """
        threading.Thread.__init__(self)
        self.pattern_matcher = re.compile(
            r'^(ST|US),(GS|[A-Z]+), (\d+\.\d+)KG,$')
        self.scale_string = 'ST,GS, 0.0KG,'
        self.ser = serial.Serial()
        self.ser.port = config.ser_port
        self.ser.open()

    def run(self):
        """
        Read serial until thread killed
        """
        while self.ser.isOpen():
            self.scale_string = self.ser.readline()

    def is_stable(self):
        """
        Return true iff the weight on the scale is stable
        """
        return self.pattern_matcher.findall(self.scale_string)[0][0] == 'ST'

    def get_weight(self):
        """
        Returns the value of the weight on the scale as float
        """
        return float(self.pattern_matcher.findall(self.scale_string)[0][2])

    def kill(self):
        """
        Called when thread must be killed. Causes loop of thread to
        terminate and thread to die
        """
        self.ser.close()

class DBAPI:
    """
    This class is a helper in accessing DB related functions of Gleba.
    """
    def __init__(self):
        self.http_address = config.django_http_path

    def add_box(self, picker, batch, variety,
                      initial_weight, final_weight, timestamp):
        """
        Performs a url request with for the django add box using all the
        info in parameters

        Returns (p,m) p is true iff the operation was successful
        else m is the error message returned from the server
        """
        params = urllib.urlencode({
            'initial_weight': initial_weight,
            'final_weight':   final_weight,
            'timestamp':      timestamp,
            'variety':        variety,
            'picker':         picker,
            'batch':          batch
        })
        full_address = self.http_address + 'add_box?{}'
        request = urllib.urlopen(full_address.format(params))
        return ((request.read() == 'success'), request.read())

    def add_boxes(self, box_list):
        """
        Performs a single request with box_list as parameters.

        box_list must be a list of dictionaries. For example:
        [{'picker': picker_id,
          'batch':  batch_id,
          'variety': variety_id,
          'initial_weight': initial_weight,
          'final_weight': final_weight,
          'timestamp': timestamp (format is "%Y-%m-%d %H:%M:%S")
        },]
        """
        full_address = self.http_address + 'add_boxes/'
        data = urllib.urlencode({'boxes': dumps(box_list)})
        request = urllib.urlopen(full_address, data)
        response = request.read()
        return True if (response == 'success\n') else response

    def get_active_pickers_xml(self):
        """
        Parse an xml list of all the current pickers into a python list.
        """
        result = []
        full_address = self.http_address + 'picker_list.xml'
        xmldoc = minidom.parse(urllib.urlopen(full_address))
        for picker in xmldoc.getElementsByTagName("picker"):
            id_elem = picker.getElementsByTagName('id')[0]
            fname_elem = picker.getElementsByTagName('first_name')[0]
            lname_elem = picker.getElementsByTagName('last_name')[0]
            result.append([id_elem.firstChild.data,
                           fname_elem.firstChild.data,
                           lname_elem.firstChild.data])
        return result

    def get_active_batches_xml(self):
        """
        Parse an xml list of all the current batches into a python list.
        """
        result = []
        full_address = self.http_address + 'batch_list.xml'
        xmldoc = minidom.parse(urllib.urlopen(full_address))
        for batch in xmldoc.getElementsByTagName("batch"):
            batch_id = batch.getElementsByTagName('id')[0].firstChild.data
            date_elem = batch.getElementsByTagName('date')[0]
            day = date_elem.getElementsByTagName('day')[0].firstChild.data
            month = date_elem.getElementsByTagName('month')[0].firstChild.data
            year = date_elem.getElementsByTagName('year')[0].firstChild.data
            room_elem = batch.getElementsByTagName('room')[0]
            room_number = (room_elem.getElementsByTagName('number')[0]
                           .firstChild.data)
            date_format = '{}/{}/{}'
            batch_date = date_format.format(day, month, year)
            result.append([batch_id, batch_date, room_number])
        return result

    def get_active_varieties_xml(self):
        """
        Parse an xml list of all varieties into a python list

        NOTE: as of 11/2/2011 the list now performs the cast to float
              for the number values
        """
        result = []
        full_address = self.http_address + 'variety_list.xml'
        xmldoc = minidom.parse(urllib.urlopen(full_address))
        for variety in xmldoc.getElementsByTagName('variety'):
            id_elem = variety.getElementsByTagName("id")[0]
            name_elem = variety.getElementsByTagName("name")[0]
            iw_elem = variety.getElementsByTagName("minimum_weight")[0]
            fw_elem = variety.getElementsByTagName("tolerance")[0]
            result.append([id_elem.firstChild.data,
                           name_elem.firstChild.data,
                           float(iw_elem.firstChild.data),
                           float(fw_elem.firstChild.data)])
        return result

    def get_active_pickers_json(self):
        """
        Simply forwards the json object to the client.
        """
        full_address = self.http_address + 'picker_list.json'
        return urllib.urlopen(full_address).read()

    def get_active_batches_json(self):
        """
        Simply forwards the json object to the client.
        """
        full_address = self.http_address + 'batch_list.json'
        return urllib.urlopen(full_address).read()

    def get_active_varieties_json(self):
        """
        Simply forwards the json object to the client.
        """
        full_address = self.http_address + 'variety_list.json'
        return urllib.urlopen(full_address).read()

    def get_active_pickers_list(self):
        """
        Returns a list of dictionaries of all active pickers.
        """
        return loads(self.get_active_pickers_json())

    def get_active_batches_list(self):
        """
        Returns a list of dictionaries of all active batches.
        """
        return loads(self.get_active_batches_json())

    def get_active_varieties_list(self):
        """
        Returns a list of dictionaries of all active varieties.
        """
        return loads(self.get_active_varieties_json())
