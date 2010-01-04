# -*- coding: utf-8 -*-

import hashlib
import time

from server.events import Message, UserConnect, UserDisconnect


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

    def __init__(self, login, first_connection=True):
        self.request = None
        self.first_connection = first_connection
        self.last_checkout_at = time.time()
        self.login = login
        self.channels = set()

    def update_request(self, request):
        self.request = request
        self.first_connection = False

    @property
    def last_checkout(self):
        return int(time.time() - self.last_checkout_at)

    def join(self, chan):
        chan.add_listener(self)
        self.channels.add(chan)

    def quit(self, chan):
        chan.remove_listener(self)
        self.channels.remove(chan)

    def add_event(self, event):
        self.request.write(event)

    def __repr__(self):
        return '<User: login=%s last_checkout=%s>' % (
            repr(self.login), self.last_checkout)

    def destroy(self):
        for chan in list(self.channels):
            self.quit(chan)
