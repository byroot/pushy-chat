from twisted.words.protocols import irc
from twisted.internet import protocol, reactor

class IRCTransport(irc.IRCClient):
    
    @property
    def nickname(self):
        return self.user.login
    
    @property
    def user(self):
        return self.factory.user

    def privmsg(self, user, channel, message):
        self.user.user_said(user, channel, message)

    def noticed(self, user, channel, message):
        self.user.user_said(user, channel, message)

    def signedOn(self):
        self.user.update_irc_transport(self)

    def joined(self, channel):
        print "Joined %s." % (channel,)

    def userJoined(self, user, channel):
        self.user.user_joined(user, chan)

    def userLeft(self, user, channel):
        self.user.user_left(user, channel)

    def userQuit(self, user, channel):
        self.user.user_left(user, channel) # TODO: disabiguation

    def irc_RPL_NAMREPLY(self, server, chan_data):
        nickname, _, chan, users = chan_data
        self.user.receive_user_list(chan, users.split())

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
        reactor.connectTCP('irc.freenode.net', 6667, cls(user))
