# -*- coding: utf-8 -*-


class Message(object):
    
    def __init__(self, login, body):
        self.login = login
        self.body = body
    
    def __unicode__(self):
        return u'%s: %s' % (self.login, self.body)

    
