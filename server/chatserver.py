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

from server.models import Channel, Message, User

class PushyChatServer(SocketServer.ThreadingMixIn, HTTPServer):
    pass


class PushyChatRequestHandler(SimpleHTTPRequestHandler):
    channels = {}
    users = []
    messages = []
    
    def log_connection_close(self, error): # TODO: nice log
        print 'connection closed by client'
    
    def log_user(self, user):
        print 'incomming user: %s' % user.login
    
    def do_GET(self):
        if not self.path.startswith('/chat/'):
            return SimpleHTTPRequestHandler.do_GET(self)
        print self.users
        self.send_response(200)
        self.send_header("Content-type", 'text/plain')
        self.end_headers()
        
        self.log_user(self.user)
        
        try:
            while True:
                messages = self.find_new_messages()
                if messages:
                    self.wfile.write(u'\n'.join(m.to_json() for m in messages))
                    self.wfile.flush()
                time.sleep(1)
                
        except socket.error, e:
            self.log_connection_close(e)

    def find_new_messages(self):
        messages = [m for m in self.messages[self.user.last_check - 1:] if m.chan in self.user.channels]
        self.user.last_check = len(self.messages) - 1
        return messages
        
    def do_POST(self):
        if not hasattr(self, 'action_%s' % self.action):
            self.send_response(404)
            self.end_headers()
        else:
            if getattr(self, 'action_%s' % self.action)():
                self.send_response(200)
            else:
                self.send_response(304)
            self.end_headers()
    
    def action_send(self):
        chan = self.get_channel(self.POST['chan'])
        self.messages.append(Message(self.user, chan, self.POST['body']))
        return True

    def action_join(self):
        print 'JOIN: %s on %s' % (self.user.login, self.POST['chan'])
        chan = self.get_channel(self.POST['chan'])
        self.user.join(chan)
        print self.user.channels
        print chan.listeners
        return True

    def get_channel(self, chan_name):
        if not chan_name in self.channels:
            chan = self.channels[chan_name] = Channel(chan_name)
        else:
            chan = self.channels[chan_name]
        return chan
    
    @property
    def user(self):
        if not hasattr(self, '_user'):
            for user in self.users:
                if user.login == self.GET['login']:
                    self._user = user
                    return self._user
        
        if not hasattr(self, '_user'):
            self._user = User(self.GET['login'], offset=len(self.messages) - 1)
            self.users.append(self._user)
        return self._user
    
    @property
    def action(self):
        if not hasattr(self, '_action'):
            path, query = urllib.splitquery(self.path)
            self._action = path.split('/')[-1]
        return self._action
    
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