# -*- coding: utf-8 -*-

import time

from server.events import Message, UserConnect, UserDisconnect, UserRenamed


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
        self.connected = False
        self.first_connection = first_connection
        self.last_checkout_at = time.time()
        self.login = login
        self.queue = []
        self.channels = set()

    def update_request(self, request):
        request.after_connection_lost = self.unset_request
        self.request = request
        self.connected = True
        self.first_connection = False
        self.flush_queue()

    def flush_queue(self):
        for event in self.queue:
            self.add_event(event)
        self.queue = []

    def unset_request(self, disconnected_request=None):
        if not disconnected_request or self.request is disconnected_request:
            self.request = None
            self.connected = False
        disconnected_request.after_connection_lost = None

    def rename(self, new_login):
        event = UserRenamed(self.login, new_login)
        for user in set(chain(c.listeners for c in self.channels)):
            user.add_event(event)

    def touch(self):
        self.last_checkout_at = time.time()

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
        if self.connected:
            self.request.write(event)
            self.touch()
        else:
            self.queue.append(event)

    def __repr__(self):
        return '<User: login=%s last_checkout=%s>' % (
            repr(self.login), self.last_checkout)

    def destroy(self):
        print self, 'DISCONNECTED'
        for chan in list(self.channels):
            self.quit(chan)
