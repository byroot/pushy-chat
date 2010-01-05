#!/usr/bin/python
# -*- coding: utf-8 -*-
import json

from twisted.web import resource, server

from server.events import Event
from server.models import User, Channel
from server.utils import JSONRequest


class JSONRequest(object, server.Request):
    channels = {}
    users = {}

    def __init__(self, *args, **kwargs):
        object.__init__(self)
        server.Request.__init__(self, *args, **kwargs)

    def write(self, content):
        if isinstance(content, Event):
            content = '(%s)' % json.dumps(content.to_dict())
        server.Request.write(self, content)

    def connectionLost(self, reason):
        server.Request.connectionLost(self, reason)
        if getattr(self, 'after_connection_lost', False):
            self.after_connection_lost(self)

    @property
    def user(self):
        return self.getSession().user

    @user.setter
    def user(self, new_user):
        session = self.getSession()
        session.user = new_user
        session.touch()

    @property
    def chan(self):
        chan_name = self.args['chan'][0]
        chan = self.channels.get(chan_name, None)
        if not chan:
            chan = self.channels[chan_name] = Channel(chan_name)
        return chan

    @classmethod
    def purge_loop(cls):
        for login, user in cls.users.items():
            if user.last_checkout > 10:
                user.destroy()
                cls.users.pop(login)

        for chan_name, chan in cls.channels.items():
            if not chan.has_listeners:
                cls.channels.pop(chan_name)


Data = JSONRequest


class Listen(resource.Resource):

    def render_GET(self, request):
        request.setHeader('Content-Type', 'application/json, text/javascript')
        request.user.update_request(request)
        return server.NOT_DONE_YET


class Login(resource.Resource):

    def render_POST(self, request):
        login = request.args["login"].pop()
        request.user = Data.users[login] = User(login)
        return ''


class Send(resource.Resource):

    def render_POST(self, request):
        request.chan.post_message(request.user, request.args['body'][0])
        return ''


class Join(resource.Resource):

    def render_POST(self, request):
        request.setHeader('Content-Type', 'application/json, text/javascript')
        request.chan.add_listener(request.user)
        message = {'listeners': [u.login for u in request.chan.listeners]}
        return '(%s)' % json.dumps(message)


class Quit(resource.Resource):

    def render_POST(self, request):
        request.chan.remove_listener(request.user)
        return ''
