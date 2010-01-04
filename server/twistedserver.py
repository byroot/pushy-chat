#!/usr/bin/python
# -*- coding: utf-8 -*-
import json

from twisted.web import resource, server

from server.models import User, Channel
from server.utils import JSONRequest


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


class Subscriber(BasePushyChatResource):

    def render_GET(self, request):
        request.setHeader('Content-Type', 'application/json, text/javascript')
        request.getSession().user.update_request(JSONRequest(request))
        return server.NOT_DONE_YET


class Login(BasePushyChatResource):

    def render_POST(self, request):
        login = request.args["login"].pop()
        session = request.getSession()
        session.user = self.users[login] = User(login)
        session.touch()
        return ''


class SendMessage(BasePushyChatResource):

    def render_POST(self, request):
        chan = self.get_or_create_chan(request)
        chan.post_message(self.get_user(request), request.args['body'][0])
        return ''


class JoinChannel(BasePushyChatResource):
    
    def render_POST(self, request):
        request.setHeader('Content-Type', 'application/json, text/javascript')
        chan = self.get_or_create_chan(request)
        chan.add_listener(self.get_user(request))
        return '(%s)' % json.dumps({'listeners': [u.login for u in chan.listeners]})


class QuitChannel(BasePushyChatResource):

    def render_POST(self, request):
        self.get_chan(request).remove_listener(self.get_user(request))
        return ''
