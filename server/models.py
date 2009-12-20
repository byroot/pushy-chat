# -*- coding: utf-8 -*-

import json
import hashlib
from itertools import chain
from UserDict import UserDict


class Message(object):

    def __init__(self, user, chan, body):
        self.user = user
        self.chan = chan
        chan.messages.add(self)
        self.body = body
    
    def __unicode__(self):
        return u'%s: %s: %s' % (self.chan.name, self.user.login, self.body)

    def __repr__(self):
        return unicode(self)

    def to_json(self):
        return u'(%s)' % json.dumps({
            'type': 'message',
            'login': self.user.login, 
            'body': self.body,
            'chan': self.chan.name
        })

    
class Channel(object):
    
    def __init__(self, name):
        self.name = name
        self.listeners = set()
        self.messages = set()

    def __repr__(self):
        return '<Channel: %s>' % self.name

class User(object):
    
    def __init__(self, login, offset=-1):
        self.login = login
        self.last_check = offset
        self.channels = set()
    
    def join(self, chan):
        self.channels.add(chan)
        chan.listeners.add(self)

    def quit(self, chan):
        self.channels.remove(chan)
        chan.listeners.remove(self)
    
    def __repr__(self):
        return '<User: %s>' % self.login
    
    @classmethod
    def generate_uid():
        return hashlib.sha256().hexdigest()