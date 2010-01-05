# -*- coding: utf-8 -*-

def lowercase(string):
    return string[0].lower() + u''.join(
        c if c.islower() else '_%c' % c.lower() for c in string[1:])


class Event(object):

    def get_type(self):
        return lowercase(self.__class__.__name__)

    @classmethod
    def _iter_bases(cls, klass=None):
        if not klass:
            klass = cls
            yield cls

        for base in klass.__bases__:
            yield base
            for parent_base in cls._iter_bases(base):
                yield parent_base

    def to_dict(self):
        data = {}
        for klass in self._iter_bases():
            if hasattr(klass, '_to_dict'):
                data.update(klass._to_dict(self))
        return data

    def _to_dict(self):
        return {'type': self.get_type()}


class HoldOn(Event):
    pass


class UserRenamed(Event):

    def __init__(self, old_login, new_login):
        self.old_login = old_login
        self.new_login = new_login

    def _to_dict(self):
        return {'old_login': self.old_login, 'new_login': self.new_login}


class UserEvent(Event):

    def __init__(self, user, chan):
        super(Event, self).__init__()
        self.user = user
        self.chan = chan

    def _to_dict(self):
        return {'login': self.user.login, 'chan': self.chan.name}


class UserDisconnect(UserEvent):
    pass


class UserConnect(UserEvent):
    pass


class Message(UserEvent):

    def __init__(self, user, chan, body):
        super(Message, self).__init__(user, chan)
        self.body = body

    def __unicode__(self):
        return u'%s: %s: %s' % (self.chan.name, self.user.login, self.body)

    def __repr__(self):
        return unicode(self)

    def _to_dict(self):
        return {'body': self.body}
