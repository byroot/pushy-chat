# -*- coding: utf-8 -*-

import json
import hashlib
from itertools import chain
from UserDict import UserDict

def lowercase(string):
    return string[0].lower() + u''.join(
        c if c.islower() else '_%c' % c.lower() for c in string[1:])


class Event(object):
    
    def to_json(self):
        dic = self._to_dict()
        dic['type'] = lowercase(self.__class__.__name__)
        return u'(%s)' % json.dumps(dic)


class UserEvent(Event):
    
    def __init__(self, user, chan):
        self.user = user
        self.chan = chan
    
    def _to_dict(self):
        return {'login': self.user.login, 'chan': self.chan.name}


class UserDisconnect(UserEvent):
    pass


class UserConnect(UserEvent):
    pass


class Message(Event):

    def __init__(self, user, chan, body):
        self.user = user
        self.chan = chan
        self.body = body
    
    def __unicode__(self):
        return u'%s: %s: %s' % (self.chan.name, self.user.login, self.body)

    def __repr__(self):
        return unicode(self)

    def _to_dict(self):
        return {
            'login': self.user.login, 
            'body': self.body,
            'chan': self.chan.name
        }

    
class Channel(object):
    
    def __init__(self, name):
        self.name = name
        self.listeners = set()

    def __repr__(self):
        return '<Channel: %s>' % self.name
    
    def add_event(self, event):
        for user in self.listeners:
            user.add_event(event)

    def post_message(self, user, body):
        self.add_event(Message(user, self, body))
        
    def add_listener(self, user):    
        self.add_event(UserConnect(user, self))
        self.listeners.add(user)
        
    def remove_listener(self, user):
        self.listeners.remove(user)
        self.add_event(UserDisconnect(user, self))


class User(object):
    
    def __init__(self, login, first_connection=False):
        self.first_connection = first_connection
        self.queue = []
        self.login = login
        self.channels = set()
    
    def join(self, chan):
        chan.add_listener(self)

    def quit(self, chan):
        chan.remove_listener(self)

    def add_event(self, event):
        self.queue.append(event)
    
    def __iter__(self):
        try:
            while True:
                yield self.queue.pop()
        except IndexError:
            pass
    
    def __repr__(self):
        return '<User: %s>' % self.login
    
    @classmethod
    def generate_uid():
        return hashlib.sha256().hexdigest()