#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import time
from datetime import datetime
import socket
from SimpleHTTPServer import SimpleHTTPRequestHandler
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer, SocketServer


class PushyChatServer(SocketServer.ThreadingMixIn, HTTPServer):
    pass


class PushyChatRequestHandler(SimpleHTTPRequestHandler):
    messages = []
    
    def log_connection_close(self, error): # TODO: nice log
        print 'connection closed by client'
    
    def do_GET(self):
        if not self.path.startswith('/chat/'):
            return SimpleHTTPRequestHandler.do_GET(self)
        
        #self.last_check = self.headers[]
        self.send_response(200)
        self.send_header("Content-type", 'text/plain')
        self.end_headers()
        try:
            while True:
                self.wfile.write(self.find_new_messages())
                time.sleep(1)
        except socket.error, e:
            self.log_connection_close(e)

    def find_new_messages(self):
        return 'foobar\n'
    
    def do_POST(self):
        params =  self._parse_params()
        self.send_new_message(params['login'], params['chan'], params['message'])
        self._redirect_to_root()

    def send_new_message(self, login, chan, message):
        self.messages.append({'login': login, 'chan': chan, 'message': message, 'time': time.time()})

    def _redirect_to_root(self):
        self.send_response(301)
        self.send_header("Location", "/")
        self.end_headers()

    def _parse_params(self):
        content_length = int(self.headers['content-length'])
        params_string = self.rfile.read(content_length)
        def parse_param(param):
            return param.split('=') if '=' in param else (param, None)
        return dict(parse_param(s) for s in params_string.split('&'))


