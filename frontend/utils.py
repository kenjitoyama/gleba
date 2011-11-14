"""
Copyright (C) 2010 Simon Dawson, Meryl Baquiran, Chris Ellis
and Daniel Kenji Toyama 
Copyright (C) 2011 Simon Dawson, Daniel Kenji Toyama

This file is part of Gleba 

Gleba is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

Gleba is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with Gleba.  If not, see <http://www.gnu.org/licenses/>.

Path: 
    frontend.utils

Purpose:
    This is a library of classes for use within the Gleba Software system
"""
import threading
import urllib, urllib2, cookielib
import re
from xml.dom import minidom
from json import dumps, loads
import serial
import config

class ThreadSerial(threading.Thread):
    """
    Opens a serial connection on the port specified in config.py.

    Starts a thread which consumes the serial port and returns the value of
    the weight as the get_weight method is called.

    If opening the serial port fails, it will throw a serial.SerialException.

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
        self.ser.port = config.SERIAL_PORT
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
        """
        Logs the user in the backend.

        config.BACKEND_USERNAME and config.BACKEND_PASSWORD will be used
        to login to the backend. Make sure that this user and password
        combination is correct, otherwise the GUI will fail to load.
        The normal login redirects the user to the profile page, but instead
        we ask the backend to redirect the user to the root URL, and we simply
        ignore it.
        """
        cjar = cookielib.CookieJar()
        login_url = config.DJANGO_HTTP_URL + 'accounts/login/?next=/'
        self.opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cjar))
        self.opener.open(login_url) # fetch csrftoken and sessionid
        csrf_token = ''
        for cookie in cjar:
            if cookie.name == 'csrftoken':
                csrf_token = cookie.value
        if csrf_token == '':
            raise Exception('No CSRF token found. Check backend URL.')
        login_data = urllib.urlencode({
            'username':            config.BACKEND_USERNAME,
            'password':            config.BACKEND_PASSWORD,
            'csrfmiddlewaretoken': csrf_token
        })
        request = self.opener.open(login_url, login_data)
        assert(request.getcode() == 200) # check if successful

    def __del__(self):
        """
        Logs the user out from the backend.
        """
        self.opener.open(config.DJANGO_HTTP_URL + 'accounts/logout/')

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
        full_address = config.DJANGO_HTTP_URL + 'add_boxes/'
        data = urllib.urlencode({'boxes': dumps(box_list)})
        request = self.opener.open(full_address, data)
        response = request.read()
        return True if (response == 'success\n') else response

    def get_active_pickers_xml(self):
        """
        Parse an xml list of all the current pickers into a python list.
        """
        result = []
        full_address = config.DJANGO_HTTP_URL + 'picker_list.xml'
        xmldoc = minidom.parse(self.opener.open(full_address))
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
        full_address = config.DJANGO_HTTP_URL + 'batch_list.xml'
        xmldoc = minidom.parse(self.opener.open(full_address))
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
        full_address = config.DJANGO_HTTP_URL + 'variety_list.xml'
        xmldoc = minidom.parse(self.opener.open(full_address))
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
        full_address = config.DJANGO_HTTP_URL + 'picker_list.json'
        return self.opener.open(full_address).read()

    def get_active_batches_json(self):
        """
        Simply forwards the json object to the client.
        """
        full_address = config.DJANGO_HTTP_URL + 'batch_list.json'
        return self.opener.open(full_address).read()

    def get_active_varieties_json(self):
        """
        Simply forwards the json object to the client.
        """
        full_address = config.DJANGO_HTTP_URL + 'variety_list.json'
        return self.opener.open(full_address).read()

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
