# -*- coding: utf-8 -*-

import time
from itertools import chain

from server.events import Message, UserConnect, UserDisconnect, UserRenamed
from server.client import IRCTransportFactory


class User(object):

    def __init__(self, login, first_connection=True):
        IRCTransportFactory.connect(self)
        self.irc_transport = None
        self.request = None
        self._last_online = None
        self.first_connection = first_connection
        self.login = login
        self.queue = []
        self.channels = set()

    def update_request(self, request):
        request.after_connection_lost = self.unset_request
        self.request = request
        self._last_online = None
        self.first_connection = False
        self.flush_queue()

    def flush_queue(self):
        for event in self.queue:
            self.add_event(event)
        self.queue = []

    def unset_request(self, disconnected_request=None):
        if not disconnected_request or self.request is disconnected_request:
            self.request = None
            self._last_online = time.time()
        disconnected_request.after_connection_lost = None

    def rename(self, new_login):
        event = UserRenamed(self.login, new_login)
        for user in set(chain.from_iterable(c.listeners for c in self.channels)):
            user.add_event(event)
        self.login = new_login

    @property
    def connected(self):
        return bool(self.request)

    @property
    def last_online(self):
        if self._last_online:
            return int(time.time() - self._last_online)
        return 0

    def update_irc_transport(self, instance):
        print 'Set irc_transport'
        self.irc = instance

    def say(self, chan, message):
        self.irc.say(chan, message)
        self.user_said(self.login, chan, message)

    def join(self, chan):
        self.irc.join(chan)
        self.channels.add(chan)

    def leave(self, chan):
        self.irc.leave(chan)
        if chan in self.channels:
            self.channels.remove(chan)

    def user_said(self, user, chan, message):
        self.add_event(Message(user, chan, message))

    def user_joined(self, user, chan):
        self.add_event(UserConnect(user, chan))

    def user_left(self, user, chan):
        self.add_event(UserDisconnect(user, chan))

    def add_event(self, event):
        if self.connected:
            self.request.write(event)
        else:
            self.queue.append(event)

    def __repr__(self):
        return '<User: login=%s last_online=%s>' % (
            repr(self.login), self.last_online)

    def __hash__(self):
        return hash('USER-%s' % self.login)

    def destroy(self):
        print self, 'DISCONNECTED'
        self.irc.quit('Client disconnected')
