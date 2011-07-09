#!/usr/bin/env python
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
from os import curdir, sep
from json import dumps
from cgi import parse_qs
import sys
sys.path.append('..')
from utils import ThreadSerial, DBAPI

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
        elif(self.path == '/active_pickers'):
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(dumps(self.db_connection.get_active_pickers()))
            return
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
        if(self.path == '/add_box'):
            length = int(self.headers.getheader('content-length'))
            post_vars = parse_qs(self.rfile.read(length), keep_blank_values = 1)
            picker_id = post_vars['picker_id'][0]
            initial_weight = post_vars['initial_weight'][0]
            final_weight = post_vars['final_weight'][0]
            variety_id = post_vars['variety_id'][0]
            batch_id = post_vars['batch_id'][0]
            timestamp = post_vars['timestamp'][0]
            response = self.db_connection.add_box(picker_id, batch_id, variety_id,
                                       initial_weight, final_weight, timestamp)
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
