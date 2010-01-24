from twisted.words.protocols import irc
from twisted.internet import protocol, reactor

class IRCTransport(irc.IRCClient):
    
    @property
    def nickname(self):
        return self.user.login
    
    @property
    def user(self):
        return self.factory.user

    def signedOn(self):
        self.user.update_irc_transport(self)

    def joined(self, channel):
        print "Joined %s." % (channel,)


class IRCTransportFactory(protocol.ClientFactory):
    protocol = IRCTransport

    def __init__(self, user):
        self.user = user

    def clientConnectionLost(self, connector, reason):
        print "Lost connection (%s), reconnecting." % (reason,)
        connector.connect()

    def clientConnectionFailed(self, connector, reason):
        print "Could not connect: %s" % (reason,)
        
    @classmethod
    def connect(cls, user):
        reactor.connectTCP('localhost', 6667, cls(user))
