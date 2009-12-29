#!/usr/bin/python
# -*- coding: utf-8 -*-

import re
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
    daemon_threads = True


class PushyChatRequestHandler(SimpleHTTPRequestHandler):
    RE_SID = re.compile(r'session_id=(\w+)')
    server_version = 'PushyChat/0.1'
    channels = {}
    users = {}
    
    def handle_one_request(self):
        self._user = None
        return SimpleHTTPRequestHandler.handle_one_request(self)
    
    @classmethod
    def purge_loop(cls):
        print '- start purge loop'
        while True:
            time.sleep(5)
            trash = [u for u in cls.users.values() if u.last_checkout > 20]
            for user in trash:
                cls.users.pop(user.session_id)
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
        
        self.send_response(200)
        self.send_header("Content-type", 'application/json, text/javascript')
        self.end_headers()

        try:
            if self.user.first_connection:
                self.wfile.write(u'(%s)' % json.dumps({'type': 'cookie',
                    'name': 'session_id', 'value': self.user.session_id}))
            while True:
                for packet in self.user:
                    self.wfile.write(u'(%s)' % json.dumps(packet))
                self.wfile.flush()                    
                self.user.last_checkout_at = time.time()
                time.sleep(1)
                
        except socket.error, e:
            self.log_connection_close(e)
    
    def do_POST(self):
        print self.user.session_id
        print self.session_id
        if not hasattr(self, 'action_%s' % self.action):
            self.send_response(404)
            self.end_headers()
        else:
            try:
                response = getattr(self, 'action_%s' % self.action)()
            except Exception, e:
                self.send_response(500)
                self.end_headers()
                raise e
                
            if not isinstance(response, dict):
                self.send_response(200 if response else 304)
                self.end_headers()
            else:
                default_response = {'code': 200, 'headers': {}, 
                                    'cookies': {}, 'body': {} }
                default_response.update(response)
                response = default_response

                self.send_response(response['code'])
                
                for name, value in response['headers'].items():
                    self.send_header(name, value)
                for name, value in response['cookies'].items():
                    self.set_cookie(name, value)
                self.end_headers()

                self.wfile.write(json.dumps(response['body']))

    def action_send(self):
        chan = self.get_channel(self.POST['chan'])
        chan.post_message(self.user, self.POST['body'])
        return True

    def action_join(self):
        chan = self.get_channel(self.POST['chan'])
        self.user.join(chan)
        return {'body': {'listeners': [u.login for u in chan.listeners]}}

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
    def session_id(self):
        try:
            return self.RE_SID.findall(self.headers['cookie']).pop()
        except:
            return None

    @property
    def user(self):
        if self._user is None:
            if self.session_id in self.users:
                self._user = self.users[self.session_id]
                self._user.first_connection = False
                print 'retreive:', self._user.login
            elif 'login' in self.GET:
                self._user = User(self.GET['login'], first_connection=True)
                print 'connect:', self._user.login
                self.users[self._user.session_id] = self._user
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
    
    def set_cookie(self, name, value):
        self.send_header('Set-Cookie', '%s=%s' % (name, value))
    
    @classmethod
    def _clean_data(cls, data):
        return dict((k, v if len(v) > 1 else v.pop()) for k, v in data.iteritems())
