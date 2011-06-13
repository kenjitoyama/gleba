#!/usr/bin/env python
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
from os import curdir, sep

HOSTNAME = 'localhost'
PORT_NUMBER = 45322 # 'gleba' in numpad letters

weight = 3.950; # just a placeholder for the real weight coming from the scale

class GUIHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if(self.path == '/weight'):
            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            global weight # dummy
            weight+=0.001 # dummy
            print(weight)
            self.wfile.write(str(weight))
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
        print(self)

if __name__=='__main__':
    try:
        http_server = HTTPServer(('', PORT_NUMBER), GUIHandler)
        print('GUI server started. Open http://{}:{}/ in your browser'.
              format(HOSTNAME, PORT_NUMBER))
        http_server.serve_forever()
    except KeyboardInterrupt:
        print('GUI server is shutting down')
        http_server.socket.close()
