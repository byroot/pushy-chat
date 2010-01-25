var EVENT_METHODS = _(['submit', 'click', 'keypress']);
    
function pushConnect(url, callback) {
    function parsePackets(packet, status, fulldata, xhr) {
        _(packet.match(/\(\{[^\)]*\}\)/g)).chain().toArray().each(function(json) {
            try{
                callback(eval(json));
            } catch(e) {
                console.log('invalid packet: ', packet, e);
            }
        });
    }
    
    function startStream(){
        var recursive = _.bind(setTimeout, window, startStream, 20);
        jQuery.get(url, recursive, parsePackets);
    }
    startStream();
}

function eventFunction(method, binding) {
    return _(_(method).bind(binding || window)).wrap(function(func, event) {
        return func(event) || false;
    });
}

function Class(klass) {
    return function() {
        var base = klass.tag ? $('<' + klass.tag + '>') : {};
        var self = $.extend(base, klass);
        _.bindAll(self);
        if (klass.tag) { // extended DOM object
            _(EVENT_METHODS.intersect(_(self).functions())).each(function(method) {
                $(self).bind(method, eventFunction(self[method]));
            });
        }
        self.initialize.apply(self, arguments);
        return self;
    };
}

var Message = Class({
    tag: 'li',

    initialize: function(login, body) {
        this.addClass('message')
            .append($('<span>').addClass('login').text('<' + login + '> '))
            .append($('<span>').addClass('message-body').text(body));
    }

});

var Notification = Class({
   tag: 'li',
   
   templates: {
       user_connect: _.template('* <%= login %> has join this channel'),
       user_disconnect: _.template('* <%= login %> has left this channel')
   },

   initialize: function(message) {
       this.addClass('notification').text(this.templates[message.type](message));
   }

});

var ChatWindow = Class({
    tag: 'div',

    initialize: function(chan) {
        this.chan = chan;
        this.addClass('window').attr('id', 'window-' + chan.name);
        this.messageList = $('<ul>').addClass('message-list').appendTo(this);
    },

    appendMessage: function(message) {
        this.messageList.append(Message(message.login, message.body));
    },

    appendNotification: function(message) {
        this.messageList.append(Notification(message));
    }

});

var UserList = Class({
    tag: 'ul',
    
    initialize: function(chan) {
        this.attr('id', 'user-list-' + chan.name).addClass('user-list');
        this.chan = chan;
        this.logins = [];
    },
    
    clean: function() {
        this.logins = _(this.logins.sort()).uniq(true);
    },
    
    sync: function() {
        this.clean();
        this.empty().append(_(this.logins).map(function(l) { return $('<li>').text(l)[0] }));
    },
    
    updateLogins: function(logins) {
        this.logins = logins;
        this.sync();
    },
    
    appendLogin: function(login) {
        this.logins.push(login);
        this.sync();
    },
    
    removeLogin: function(login) {
        this.logins = _(this.logins).without(login);
        this.sync();
    }

});

var Tab = Class({
    tag: 'li',
    
    initialize: function(chan, client) {
        this.attr('id', 'tab-' + chan.name).addClass('tab');
        this.chan = chan;
        this.client = client;
        $('<button>').text(chan.name).appendTo(this);
    },
    
    click: function(event) {
        this.client.chans.select(this.chan.name);
    }

})

var Chan = Class({
    
    initialize: function(container, name) {
        this.container = container;
        this.name = name;
        this.elements = _([
            this.tab = Tab(this, container.client),
            this.window = ChatWindow(this),
            this.userList = UserList(this)
        ]);
        this.appendTo(container);
    },
    
    getLogins: function() {
      return _.clone(this.userList.logins);
    },
    
    appendTo: function(chanContainer) {
        chanContainer.tabs.append(this.tab);
        chanContainer.windows.append(this.window);
        chanContainer.userLists.append(this.userList);
        return this;
    },
    
    remove: function() {
        this.elements.invoke('remove');
    },
    
    show: function() {
        this.elements.invoke('show');
        return this;
    },
    
    setListeners: function(listeners) {
        this.userList.updateLogins(listeners);
    },
    
    handle_message: function(message) {
        this.window.appendMessage(message);
    },
    
    handle_user_connect: function(message) {
        this.userList.appendLogin(message.login);
        this.window.appendNotification(message);
    },

    handle_user_disconnect: function(message) {
        this.userList.removeLogin(message.login);
        this.window.appendNotification(message);
    }

});

var WindowContainer = Class({
    tag: 'div',
    
    initialize: function() {
        this.attr('id', 'window-container');
    },
    
    remove: function(chan) {
        this.find('#window-' + chan).remove();
    },

    select: function(chan) {
        $('#window-container > .window').hide().filter('#window-' + chan).show();
    }

});


var UserListContainer = Class({
    tag: 'div',
    
    initialize: function() {
        this.attr('id', 'user-list-container');
    },
    
    remove: function(chan) {
        this.find('#user-list-' + chan).remove();
    },
    
    select: function(chan) {
        $('#user-list-container > .user-list').hide()
            .filter('#user-list-' + chan).show();
    }
    
});

var NewTabDialog = Class({
    tag: 'div',
    
    initialize: function(callback) {
        this.callback = callback;
        var form = $('<form>').append('<p><input name="chan" type="text"/></p><p><input type="submit"></p>');
        this.attr('title', 'Chan name').append(form).dialog()
            .find(':input[name=chan]').focus();
    },
    
    submit: function(event) {
        var chan_name = this.dialog('close').find(':input[name=chan]').val();
        this.callback(chan_name);
    }

});

var TabContainer = Class({
    tag: 'ul',
    
    initialize: function(container) {
        this.attr('id', 'tablist');
        this.newTabAction = $(this.item('New tab')).click(container.open).appendTo(this);
        this.closeTabAction = $(this.item('Close tab')).click(container.close).appendTo(this);
    },
    
    item: function(label) { 
        var tpl = _.template('<li id="<%= id %>"><button><%= label %></button></li>');
        return tpl({ label: label, id: label.replace(' ', '-').toLowerCase() });
    },
    
    append: function(tab) {
        this.find('#close-tab').before(tab);
    },
    
    getFallbackTab: function() {
        var tab = this.find('.tab.selected');
        return tab.prev('.tab').text() || tab.next('.tab').text() || null
    },
    
    remove: function(chan_name) {
        this.find('#tab-' + chan_name).remove();
    },
    
    select: function(chan_name) {
        $('#tablist > .tab').removeClass('selected')
            .filter('#tab-' + chan_name).addClass('selected');
    }
    
});

var ChanContainer = Class({
    
    initialize: function(client) {
        this.client = client;
        this.chans = {};
        this.messageForm = MessageForm(this.client);
        this.containers = _([
            this.tabs = TabContainer(this),
            this.windows = WindowContainer(),
            this.userLists = UserListContainer()
        ]);
        this.containers.invoke('appendTo', client);
    },
    
    get: function(chan_name) {
        if (!chan_name) {
            return this.currentChan || null;
        }
        
        if (_(this.chans[chan_name]).isUndefined()) {
            if (_(this.chans).isEmpty()) {
                this.messageForm.enable();
            }
            this.chans[chan_name] = Chan(this, chan_name);
        }
        return this.chans[chan_name];
    },
    
    remove: function(chan_name) {
        var nextTab = this.tabs.getFallbackTab();
        if (nextTab) this.select(nextTab);
        
        this.containers.invoke('remove', chan_name);
        delete this.chans[chan_name];
        
        if (_(this.chans).isEmpty()) {
            this.messageForm.disable();
            $('li#new-tab > button').focus();
        }
        return this;
    },
    
    select: function(chan_name) {
        this.currentChan = this.get(chan_name).show();
        this.containers.invoke('select', chan_name);
        this.messageForm.focus();
        return this.currentChan;
    },
    
    close: function(event) {
        this.client.left(this.get());
        this.remove(this.get().name);
    },
    
    open: function(event) {
        NewTabDialog(this.client.join);
    }
    
});

var MessageForm = Class({
    tag: 'div',
    
    initialize: function(client) {
        this.attr('id', 'message-form');
        this.client = client;
        this.messageField = $('<input id="message" type="text" name="message">');
        this.append($('<form>').append(this.messageField, '<input type="submit">')).appendTo(client);
        this.disable();
    },
    
    keypress: function(event) {
        if (event.which != 0) return true;
        this.complete();
        return false;
    },
    
    complete: function(event) {
        
        var content = this.messageField.val();
        var isFirstWord = !content.match(/ /);
        var toComplete = content.split(/ /).pop();
        var loginList = this.client.chans.get().getLogins();
        var mask = RegExp('^' + toComplete);
        
        var matchingLogins = _(loginList).select(function(l) { return !!l.match(mask); });
        if (_(matchingLogins).isEmpty()) return false;
        
        if (matchingLogins.length == 1) {
            var replacement = matchingLogins.pop() + (isFirstWord ? ': ' : ' ');
        } else {
            var replacement = _(_.zip.apply(null,matchingLogins)).chain().map(_.uniq)
                .reject(function(i) { return this.endReached |= i.length > 1 }, {})
                .flatten().join('').value();
        }
        this.messageField.val(content.replace(toComplete, replacement));
    },
    
    focus: function() {
        this.enable();
        this.messageField.focus();
    },
    
    clear: function() {
        this.messageField.val('');
    },
    
    disable: function() {
        this.find('input').attr('disabled', 'disabled');
    },
    
    enable: function() {
        this.find('input').attr('disabled', '');
    },
    
    submit: function(event) {
        this.client.say(this.messageField.val(), this.clear);
    }
    
});

var LoginForm = Class({
    tag: 'form',
    
    initialize: function(parentNode, callback) {
        this.callback = callback;
        this.action = '#';
        this.append('<label for="login">Login:</label>',
                     '<input name="login" type="text">',
                     '<input name="connect" type="submit">')
            .appendTo(parentNode);
        this.focus();
    },
    
    focus: function() {
        this.find(':input[name=login]').focus();
    },
    
    submit: function(event) {
        var login = this.find(':input[name=login]').val();
        login && this.remove().callback(login);
    }
    
});

var Client = Class({
    tag: 'div',
    
    initialize: function(parentNode, login) {
        this.login = login;
        this.chans = ChanContainer(this);
        this.appendTo(parentNode);
        $('li#new-tab > button').focus();
        this.connect();
    },
    
    setRecap: function(data, textStatus) {
        _(data.channels).each(this.join);
        this.subscribe();
    },
    
    connect: function() {
        $.post(this.url('login'), { login: this.login }, this.setRecap, 'json');
    },
    
    subscribe: function() {
        pushConnect(this.url(), this.dispatchPacket);
    },
    
    dispatchPacket: function(packet) {
        if (_.isUndefined(packet.chan)) {
            this['handle_' + packet.type](packet);            
        } else {
            this.chans.get(packet.chan)['handle_' + packet.type](packet);
        }
    },
    
    handle_hold_on: function(message) {},
    
    url: function(action) {
        return '/chat/' + (action || '');
    },
    
    join: function(chan_name) {
        var chan = this.chans.select(chan_name);
        var callback = function(data) { chan.setListeners(data.listeners) };
        jQuery.post(this.url('join'), { chan: chan.name }, callback, 'json');
    },
    
    left: function(chan) {
        jQuery.post(this.url('left'), { chan: chan.name });
    },
    
    say: function(body, callback) {
        jQuery.post(this.url('say'), { body: body, chan: this.chans.get().name }, callback);
    }
    
});


jQuery(function($){
    jQuery.ui.dialog.defaults.bgiframe = true;
    jQuery.enableAjaxStream(true);
    
    LoginForm('body', function(login) {
        Client('body', login);
    });
});