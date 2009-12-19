#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import time
from datetime import datetime
import socket
import urllib
import urlparse

from collections import defaultdict
from SimpleHTTPServer import SimpleHTTPRequestHandler
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer, SocketServer

from server.models import Channel, Message

class PushyChatServer(SocketServer.ThreadingMixIn, HTTPServer):
    pass


class PushyChatRequestHandler(SimpleHTTPRequestHandler):
    channels = defaultdict(Channel)
    
    def log_connection_close(self, error): # TODO: nice log
        print 'connection closed by client'
    
    def do_GET(self):
        if not self.path.startswith('/chat/'):
            return SimpleHTTPRequestHandler.do_GET(self)
        
        self.send_response(200)
        self.send_header("Content-type", 'text/plain')
        self.end_headers()
        
        chan = self.path.split('/')[-1] 
        self.last_check = int(self.GET.get('last_check', self.channels[chan].last_index()))
        try:
            while True:
                message = self.find_new_message(chan)
                if message:
                    self.wfile.write(message.to_json())
                    self.wfile.flush()
                    self.last_check += 1
                time.sleep(1)
                
        except socket.error, e:
            self.log_connection_close(e)

    def find_new_message(self, chan):
        return self.channels[chan].get(self.last_check + 1)
        
    def do_POST(self):
        self.channels[self.POST['chan']].append(Message(self.POST['login'], self.POST['message']))
        self.send_response(200)
        self.end_headers()
    
    @property
    def GET(self):
        if not hasattr(self, '_post_get'):
            self._get_data = {}
            path, query = urllib.splitquery(self.path)
            self._get_data = self._clean_data(urlparse.parse_qs(query or ''))
        return self._get_data

    @property
    def POST(self):
        if not hasattr(self, '_post_data'):
            content_length = int(self.headers['content-length'])
            query = self.rfile.read(content_length)
            self._post_data = self._clean_data(urlparse.parse_qs(query))
        return self._post_data

    @classmethod
    def _clean_data(cls, data):
        return dict((k, v if len(v) > 1 else v.pop()) for k, v in data.iteritems())