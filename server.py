#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
from SimpleHTTPServer import SimpleHTTPRequestHandler
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer, SocketServer

PUBLIC_DIRECTORY = os.path.abspath(os.path.join(os.path.dirname(__file__), 'public'))

class PushyChatServer(SocketServer.ThreadingMixIn, HTTPServer):
    pass


class PushyChatRequestHandler(SimpleHTTPRequestHandler):
    
    def do_GET(self):
        if not self.path.startswith('/chat/'):
            return SimpleHTTPRequestHandler.do_GET(self)
        
    def do_POST(self):
        print self._parse_params()
        self._redirect_to_root()

    def _redirect_to_root(self):
        self.send_response(301)
        self.send_header("Location", "/")
        self.end_headers()

    def _parse_params(self):
        content_length = int(self.headers['content-length'])
        params_string = self.rfile.read(content_length)
        def parse_param(param):
            return param.split('=') if '=' in param else (param, None)
        return dict(parse_param(s) for s in params_string.split('&'))


if __name__ == '__main__':
    print 'serve content of: %s' % PUBLIC_DIRECTORY
    os.chdir(PUBLIC_DIRECTORY)
    server = PushyChatServer(('', 8000), PushyChatRequestHandler)
    server.serve_forever()
