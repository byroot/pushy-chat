# -*- coding: utf-8 -*-

import hashlib
import time


def lowercase(string):
    return string[0].lower() + u''.join(
        c if c.islower() else '_%c' % c.lower() for c in string[1:])


class Event(object):

    def get_type(self):
        return lowercase(self.__class__.__name__)


class UserEvent(Event):

    def __init__(self, user, chan):
        super(UserEvent, self).__init__()
        self.user = user
        self.chan = chan

    def _to_dict(self):
        return {
            'type': self.get_type(),
            'login': self.user.login,
            'chan': self.chan.name
        }


class UserDisconnect(UserEvent):
    pass


class UserConnect(UserEvent):
    pass


class Message(Event):

    def __init__(self, user, chan, body):
        super(Message, self).__init__()
        self.user = user
        self.chan = chan
        self.body = body

    def __unicode__(self):
        return u'%s: %s: %s' % (self.chan.name, self.user.login, self.body)

    def __repr__(self):
        return unicode(self)

    def _to_dict(self):
        return {
            'type': self.get_type(),
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

    @property
    def has_listeners(self):
        return bool(len(self.listeners))

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
        self.session_id = self.hash(login)
        self.first_connection = first_connection
        self.last_checkout_at = time.time()
        self.queue = []
        self.login = login
        self.channels = set()

    @staticmethod
    def hash(string):
        salt = hashlib.sha1("C'est tout ce que ça te fait quand je te dit"\
        " qu'on va manger des chips ?").hexdigest()
        return hashlib.sha1(str(time.time()) + string + salt).hexdigest()

    @property
    def last_checkout(self):
        return int(time.time() - self.last_checkout_at)

    def join(self, chan):
        chan.add_listener(self)

    def quit(self, chan):
        chan.remove_listener(self)

    def add_event(self, event):
        self.queue.append(event)

    def __iter__(self):
        try:
            while True:
                yield self.queue.pop()._to_dict()
        except IndexError:
            pass

    def __repr__(self):
        return '<User: login=%s last_checkout=%s>' % (
            repr(self.login), self.last_checkout)

    def destroy(self):
        for chan in self.channels:
            self.quit(chan)
