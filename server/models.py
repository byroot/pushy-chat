# -*- coding: utf-8 -*-

from itertools import chain
from UserDict import UserDict


class Message(object):
    
    def __init__(self, login, body):
        self.login = login
        self.body = body
    
    def __unicode__(self):
        return u'%s: %s' % (self.login, self.body)
    
class Channel(UserDict, object):

    def last_index(self):
        return max(chain(self.keys(), [-1]))

    def append(self, item):
        self[self.last_index() + 1] = item

