#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import time
import json
from datetime import datetime
import socket
import urllib
import urlparse

from collections import defaultdict
from SimpleHTTPServer import SimpleHTTPRequestHandler
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer, SocketServer

from server.models import Channel, Message, User, UserConnect, UserDisconnect


class PushyChatServer(SocketServer.ThreadingMixIn, HTTPServer):
    pass


class PushyChatRequestHandler(SimpleHTTPRequestHandler):
    channels = {}
    users = []
    
    @classmethod
    def purge_loop(cls):
        print '- start purge loop'
        while True:
            time.sleep(5)
            trash = [u for u in cls.users if u.last_checkout > 20]
            for user in trash:
                cls.users.remove(user)
                user.destroy()
                'DISCONNECT: %s' % user.login
            del trash
            
            for chan in [c.name for c in cls.channels.values() if not len(c.listeners)]:
                del cls.channels[chan]
    
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
                packet = {'messages': list(self.user)}
                self.wfile.write(u'(%s)' % json.dumps(packet))
                self.wfile.flush()                    
                self.user.last_checkout_at = time.time()
                time.sleep(1)
                
        except socket.error, e:
            self.log_connection_close(e)
        
    def do_POST(self):
        if not hasattr(self, 'action_%s' % self.action):
            self.send_response(404)
            self.end_headers()
        else:
            response = getattr(self, 'action_%s' % self.action)()
            if response:
                self.send_response(200)
            else:
                self.send_response(304)
            self.end_headers()
            if isinstance(response, dict):
                self.wfile.write(json.dumps(response))
            
    
    def action_send(self):
        chan = self.get_channel(self.POST['chan'])
        chan.post_message(self.user, self.POST['body'])
        return True

    def action_join(self):
        chan = self.get_channel(self.POST['chan'])
        self.user.join(chan)
        return {'listeners': [u.login for u in chan.listeners]}

    def action_quit(self):
        self.user.quit(self.get_channel(self.POST['chan']))
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
            self._user = User(self.GET['login'], first_connection=True)
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
