#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import time
from datetime import datetime
import socket
from itertools import chain
from collections import defaultdict
from SimpleHTTPServer import SimpleHTTPRequestHandler
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer, SocketServer


class PushyChatServer(SocketServer.ThreadingMixIn, HTTPServer):
    pass


class PushyChatRequestHandler(SimpleHTTPRequestHandler):
    channels = defaultdict(dict)
    
    def log_connection_close(self, error): # TODO: nice log
        print 'connection closed by client'
    
    def do_GET(self):
        if not self.path.startswith('/chat/'):
            return SimpleHTTPRequestHandler.do_GET(self)
        
        self.send_response(200)
        self.send_header("Content-type", 'text/plain')
        self.end_headers()
        
        chan = self.path.split('/')[-1] 
        self.last_check = int(self.GET.get('last_check', self.last_index_of(chan)))
        try:
            while True:
                message = self.find_new_message(chan)
                if message:
                    self.wfile.write(unicode(message))
                    self.wfile.flush()
                    self.last_check += 1
                time.sleep(1)
                
        except socket.error, e:
            self.log_connection_close(e)

    def last_index_of(self, chan):
        return max(chain(self.channels[chan].keys(), [-1]))

    def find_new_message(self, chan):
        return self.channels[chan].get(self.last_check + 1, False)
        
    def do_POST(self):
        self.send_new_message(self.POST['login'], self.POST['chan'], self.POST['message'])
        self._redirect_to_root()

    def send_new_message(self, login, chan, message):
        self.channels[chan][self.last_index_of(chan) + 1] = {'login': login, 'message': message}
        print self.channels

    def _redirect_to_root(self):
        self.send_response(301)
        self.send_header("Location", "/")
        self.end_headers()

    @property
    def GET(self):
        if not hasattr(self, '_post_get'):
            self._get_data = {}
            if '?' in self.path:
                params_string = self.path.split('?')[1]
                self._post_data = self._parse_params(params_string)
        return self._get_data

    @property
    def POST(self):
        if not hasattr(self, '_post_data'):
            content_length = int(self.headers['content-length'])
            params_string = self.rfile.read(content_length)
            self._post_data = self._parse_params(params_string)
        return self._post_data

    @classmethod
    def _parse_params(cls, params_string):
        def parse_param(param):
            return param.split('=') if '=' in param else (param, None)
        return dict(parse_param(s) for s in params_string.split('&'))


