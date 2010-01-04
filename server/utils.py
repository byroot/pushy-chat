# -*- coding: utf-8 -*-

import json

from server.events import Event


class JSONRequest(object):

    def __init__(self, request):
        self._request = request

    def __getattr__(self, name):
        if hasattr(self._request, name):
            return getattr(self._request, name)
        raise AttributeError
    
    def write(self, content):
        if isinstance(content, Event):
            content = '(%s)' % json.dumps(content.to_dict())
        self._request.write(content)

