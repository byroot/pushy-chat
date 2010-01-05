#!/usr/bin/python
# -*- coding: utf-8 -*-
import json

from twisted.web import resource, server

from server.events import Event
from server.models import User, Channel
from server.utils import JSONRequest


class JSONRequest(server.Request):

    def write(self, content):
        if isinstance(content, Event):
            content = '(%s)' % json.dumps(content.to_dict())
        server.Request.write(self, content)

    def connectionLost(self, reason):
        print 'CONNECTION LOST !!!!!!!!!'
        server.Request.connectionLost(self, reason)
        if getattr(self, 'after_connection_lost', False):
            self.after_connection_lost(self)


class BasePushyChatResource(resource.Resource):
    channels = {}
    users = {}

    @classmethod
    def get_chan(cls, request):
        chan_name = request.args['chan'].pop()
        return cls.channels[chan_name]

    @classmethod
    def get_or_create_chan(cls, request):
        chan_name = request.args['chan'].pop()
        chan = cls.channels.get(chan_name, None)
        if not chan:
            chan = cls.channels[chan_name] = Channel(chan_name)
        return chan

    @staticmethod
    def get_user(request):
        return request.getSession().user

    @classmethod
    def purge_loop(cls):
        for login, user in cls.users.items():
            if user.last_checkout > 10:
                user.destroy()
                cls.users.pop(login)

        for chan_name, chan in cls.channels.items():
            if not chan.has_listeners:
                cls.channels.pop(chan_name)


class Listen(BasePushyChatResource):

    def render_GET(self, request):
        request.setHeader('Content-Type', 'application/json, text/javascript')
        request.getSession().user.update_request(request)
        return server.NOT_DONE_YET

    def clean(self):
        print 'loop over users'
        for user in self.users.values():
            print user.login, ': ', 'disconnected' if user.request._disconnected else 'online'


class Login(BasePushyChatResource):

    def render_POST(self, request):
        login = request.args["login"].pop()
        session = request.getSession()
        session.user = self.users[login] = User(login)
        session.touch()
        return ''


class Send(BasePushyChatResource):

    def render_POST(self, request):
        chan = self.get_or_create_chan(request)
        chan.post_message(self.get_user(request), request.args['body'][0])
        return ''


class Join(BasePushyChatResource):

    def render_POST(self, request):
        request.setHeader('Content-Type', 'application/json, text/javascript')
        chan = self.get_or_create_chan(request)
        chan.add_listener(self.get_user(request))
        message = {'listeners': [u.login for u in chan.listeners]}
        return '(%s)' % json.dumps(message)


class Quit(BasePushyChatResource):

    def render_POST(self, request):
        self.get_chan(request).remove_listener(self.get_user(request))
        return ''
