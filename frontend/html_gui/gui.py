#!/usr/bin/env python
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
    frontend.html_gui.gui

Purpose:
    WebGUI server.
    This file is needed for the WebGUI interface and must be run
    before the page is open in a web browser.
"""
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
from os import curdir, sep
from json import dumps, loads
from cgi import parse_qs
import sys
sys.path.append('..')
from utils import ThreadSerial, DBAPI
from config import BOX_WEIGHT

HOSTNAME = '0.0.0.0'
PORT_NUMBER = 45322 # 'gleba' in numpad letters

class GUIHandler(BaseHTTPRequestHandler):
    serial_thread = ThreadSerial()
    serial_thread.daemon = True
    serial_thread.start()
    db_connection = DBAPI()

    def close_serial():
        self.serial_thread.kill()
    def do_GET(self):
        if(self.path == '/weight'):
            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(str(self.serial_thread.get_weight()))
            return
        elif(self.path == '/active_pickers'):
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(dumps(self.db_connection.get_active_pickers()))
            return
        elif(self.path == '/active_batches'):
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(dumps(self.db_connection.get_active_batches()))
            return
        elif(self.path == '/active_varieties'):
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(dumps(self.db_connection.get_active_varieties()))
            return
        elif(self.path == '/active_pickers.json'):
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(self.db_connection.get_active_pickers_json())
            return
        elif(self.path == '/active_batches.json'):
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(self.db_connection.get_active_batches_json())
            return
        elif(self.path == '/active_varieties.json'):
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(self.db_connection.get_active_varieties_json())
            return
        elif(self.path == '/box_weight'):
            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(BOX_WEIGHT)
        elif(self.path == '/gui.html'):
            req_file = open(curdir + sep + self.path)
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
        elif(self.path == '/gui.css'):
            req_file = open(curdir + sep + self.path)
            self.send_response(200)
            self.send_header('Content-type', 'text/css')
        elif(self.path == '/gui.js'):
            req_file = open(curdir + sep + self.path)
            self.send_response(200)
            self.send_header('Content-type', 'text/javascript')
        elif(self.path == '/button.ogg' or
             self.path == '/green.ogg' or
             self.path == '/success.ogg'):
            req_file = open('../' + curdir + sep + self.path)
            self.send_response(200)
            self.send_header('Content-type', 'application/ogg')
        else:
            self.send_response(400)
            return
        self.end_headers()
        self.wfile.write(req_file.read())
        req_file.close()

    def do_POST(self):
        if(self.path == '/add_boxes'):
            length = int(self.headers.getheader('content-length'))
            boxes = loads(self.rfile.read(length))
            response = self.db_connection.add_boxes(boxes)
            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write('true')

if __name__=='__main__':
    try:
        http_server = HTTPServer((HOSTNAME, PORT_NUMBER), GUIHandler)
        print('GUI server started. Open http://{}:{}/gui.html in your browser'.
              format(HOSTNAME, PORT_NUMBER))
        http_server.serve_forever()
    except KeyboardInterrupt:
        print('GUI server is shutting down')
        http_server.socket.close()
