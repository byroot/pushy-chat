#!/usr/bin/python
# -*- coding: utf-8 -*-
import json

from twisted.web import resource, server

from server.events import Event, HoldOn
from server.models import User
from server.utils import JSONRequest


class Data:
    users = {}

    @classmethod
    def rename(cls, old_login, new_login):
        user = cls.users[new_login] = cls.users.pop(old_login)
        user.rename(new_login)

    @classmethod
    def purge_loop(cls):
        for login, user in cls.users.items():
            user.add_event(HoldOn())
            if user.last_online > 15:
                user.destroy()
                cls.users.pop(login)


class JSONRequest(object, server.Request):

    def __init__(self, *args, **kwargs):
        object.__init__(self)
        server.Request.__init__(self, *args, **kwargs)

    def write(self, content):
        server.Request.write(self, self.to_json(content))

    def connectionLost(self, reason):
        server.Request.connectionLost(self, reason)
        if getattr(self, 'after_connection_lost', False):
            self.after_connection_lost(self)

    @property
    def user(self):
        try:
            return self.getSession().user
        except AttributeError:
            return None

    @user.setter
    def user(self, new_user):
        session = self.getSession()
        session.user = new_user
        session.touch()

    @property
    def chan(self):
        return self.args['chan'][0]

    @staticmethod
    def to_json(content):
        if isinstance(content, (Event, dict)):
            if isinstance(content, Event):
                content = content.to_dict()
            content = '(%s)' % json.dumps(content)
        return content or ''

    @staticmethod
    def action(method):
        def placeholder(self, request):
            request.write(method(self, request))
            return ''
        return placeholder


class Listen(resource.Resource):

    def render_GET(self, request):
        request.setHeader('Content-Type', 'application/json, text/javascript')
        request.user.update_request(request)
        return server.NOT_DONE_YET


class Login(resource.Resource):

    @JSONRequest.action
    def render_POST(self, request):
        login = request.args.get('login', [None]).pop()
        if request.user and request.user.login == login:
            # MAYBE: destroy old user ?
            return {'channels': list(request.user.channels)}

        request.user = Data.users[login] = User(login)
        return {'channels': []}
        #if not request.user.login == login:
        #    Data.rename(request.user.login, login)
        # TODO: handle possible errors like nickname already in use


class Say(resource.Resource):

    @JSONRequest.action
    def render_POST(self, request):
        request.user.say(request.chan, request.args['body'][0])


class Join(resource.Resource):

    @JSONRequest.action
    def render_POST(self, request):
        request.setHeader('Content-Type', 'application/json, text/javascript')
        request.user.join(request.chan)
        return {'listeners': [request.user.login]} # FIXME: find chan's user list


class Leave(resource.Resource):

    @JSONRequest.action
    def render_POST(self, request):
        request.user.leave(request.chan)
