#!/usr/bin/python
# -*- coding: utf-8 -*-

from os.path import abspath, join, dirname

from twisted.web import resource, server, static
from twisted.application import internet, service
from twisted.internet import reactor

from server.resources import Listen, Login, Send, Join, Quit, Data, JSONRequest

PUBLIC_DIRECTORY = abspath(join(dirname(__file__), '..', 'public'))

#if __name__ == '__main__':
print '- public directory: %s' % PUBLIC_DIRECTORY

root = static.File(PUBLIC_DIRECTORY)
chat = resource.NoResource()
root.putChild('chat', chat)
server.Site.requestFactory = JSONRequest
site = server.Site(root)

children = (('', Listen()),
            ('login', Login()),
            ('send', Send()),
            ('join', Join()),
            ('quit', Quit()))

for name, child in children:
    chat.putChild(name, child)

application = service.Application('pushy-chat')
httpServer = internet.TCPServer(8000, site).setServiceParent(application)
purgeLoop = internet.TimerService(20, Data.purge_loop).setServiceParent(application)
