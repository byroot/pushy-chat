
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
    
    jQuery.enableAjaxStream(true);
    function startStream(){
        var recursive = _.bind(setTimeout, window, startStream, 20);
        jQuery.get(url, recursive, parsePackets);
    }
    startStream();
}


function Class(klass) {
    
    klass.New = function() {
        var self = $.extend($('<' + klass.tag + '>'), klass)
        _.bindAll(self);
        self.initialize.apply(self, arguments);
        return self;
    };
    
    return klass;
}

var Message = Class({
    tag: 'li',
    
    initialize: function(login, body) {
        $(this).addClass('message')
            .append($('<span>').addClass('login').text('<' + login + '> '))
            .append($('<span>').addClass('message-body').text(body));
    }
});

var Notification = Class({
   tag: 'li',
   
   templates: {
       user_connect: _.template('* <%= login %> has join this channel'),
       user_disconnect: _.template('* <%= login %> has quit this channel')
   },
   
   initialize: function(message) {
       $(this).addClass('notification')
        .text(this.templates[message.type](message));
   }
    
});

var ChatWindow = Class({
    tag: 'div',
    
    initialize: function(client, chan) {
        this.client = client;
        this.chan = chan;
        $(this).addClass('window').attr('id', 'window-' + chan);
        this.messageList = $('<ul>').addClass('message-list').appendTo(this);
    },
    
    appendMessage: function(message) {
        this.messageList.append(Message.New(message.login, message.body));
    },
    
    appendNotification: function(message) {
        this.messageList.append(Notification.New(message));
    }
    
});

var WindowContainer = Class({
    tag: 'div',
    
    initialize: function(client) {
        this.windows = {};
        this.client = client;
        $(this).attr('id', 'window-container');
    },
    
    append: function(chan) {
        $(this).append(this.windows[chan] = ChatWindow.New(this, chan));
        return this.windows[chan];
    },
    
    remove: function(chan) {
        $(this).find('#window-' + chan).remove()
    },
    
    appendMessage: function(message) {
        this.windows[message.chan].appendMessage(message);
    },
    
    appendNotification: function(message) {
        this.windows[message.chan].appendNotification(message);        
    },
    
    select: function(chan) {
        this.activeWindow = this.windows[chan];
        $('#window-container > .window').hide();
        $('#window-container > #window-' + chan).show();
    }
    
});

var UserList = Class({
    tag: 'ul',
    
    initialize: function(client, chan) {
        this.attr('id', 'user-list-' + chan).addClass('user-list');
        this.client = client;
        this.chan = chan;
        this.logins = [];
    },
    
    clean: function() {
        this.logins = _(this.logins.sort()).uniq(true);
    },
    
    sync: function() {
        this.clean();
        $(this).empty();
        _(this.logins).each(_.bind(function(l) { $(this).append($('<li>').text(l)) }, this));
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

var UserListContainer = Class({
    tag: 'div',
    
    initialize: function(client) {
        this.attr('id', 'user-list-container');
        this.client = client;
        this.lists = {};
    },
    
    getCurrentLogins: function() {
      return _.clone(this.activeList.logins);
    },
    
    append: function(chan) {
        $(this).append(this.lists[chan] = UserList.New(this, chan));
        return this.lists[chan];
    },
    
    remove: function(chan) {
        $(this).find('#user-list-' + chan).remove();
    },
    
    select: function(chan) {
        this.activeList = this.lists[chan];
        $('#user-list-container > .user-list').hide();
        $('#user-list-container > #user-list-' + chan).show();
    }
    
});

var Tab = Class({
    tag: 'li',
    
    initialize: function(client, chan) {
        this.attr('id', 'tab-' + chan).addClass('tab');
        this.chan = chan;
        this.client = client;
        $(this).append($('<button>').text(chan));
        $(this).click(this.activate);
    },
    
    activate: function() {
        this.client.switchTo(this.chan);
    }
})

var TabList = Class({
    tag: 'ul',
    
    initialize: function(client) {
        $(this).attr('id', 'tablist');
        this.client = client;
        this.tabs = {};
        var item = function(label) { 
            var tpl = _.template('<li id="<%= id %>"><button><%= label %></button></li>');
            return tpl({ label: label, id: label.replace(' ', '-').toLowerCase() });
        };
        this.newTabAction = $(item('New tab')).click(this.askChanName).appendTo(this);
        this.closeTabAction = $(item('Close tab')).click(this.closeTab).appendTo(this);

    },
    
    closeTab: function(event) {
        this.client.quit(this.client.selectedChan);
    },
    
    askChanName: function(event) {
        var client = this.client;
        var form = $('<form>').submit(function(event) {
            event.preventDefault();
            client.join($(this).find(':input[name=chan]').val());
            $(this).parent('div').dialog('close');
            return false;
        });
        form.append($('<p><input name="chan" type="text"/></p>'));
        form.append($('<p><input type="submit"></p>'));
        
        $.ui.dialog.defaults.bgiframe = true;
        $('<div title="Chan name">').append(form).dialog().find(':input[name=chan]').focus();
    },
    
    append: function(chan) {
        $(this).find('#close-tab').before(this.tabs[chan] = Tab.New(this.client, chan));
        return this.tabs[chan];
    },
    
    remove: function(chan) {
        var tab = $(this).find('.tab.selected');
        this.client.switchTo(tab.prev('.tab').text() || tab.next('.tab').text());
        $(this).find('#tab-' + chan).remove();
    },
    
    select: function(chan) {
        $('#tablist > .tab').removeClass('selected');
        $('#tablist > #tab-' + chan).addClass('selected');        
    }
    
});

var MessageForm = Class({
    tag: 'div',
    
    initialize: function(client) {
        $(this).attr('id', 'message-form');
        this.client = client;
        this.form = $('<form>').submit(this.send).keypress(this.complete);
        this.messageField = $('<input id="message" type="text" name="message">').appendTo(this.form);
        $('<input type="submit">').appendTo(this.form);
        this.form.appendTo(this);
        this.disable();
    },
    
    complete: function(event) {
        if (event.keyCode != 9) return true;
        
        var content = this.messageField.val();
        var isFirstWord = !content.match(/ /);
        var toComplete = content.split(/ /).pop();
        var loginList = this.client.userListContainer.getCurrentLogins();
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
        
        return false;
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
        $('li#new-tab > button').focus();
    },
    
    enable: function() {
        this.find('input').attr('disabled', '');
    },
    
    send: function(event) {
        event.preventDefault();
        this.client.send(
            this.client.selectedChan,
            this.messageField.val(), 
            this.clear
        );
        return false;
    }
    
});

var LoginForm = Class({
    tag: 'form',
    
    initialize: function(callback) {
        this.action = '#';
        $('<label for="login">').text("Login:").appendTo(this);
        $('<input name="login" type="text">').appendTo(this);
        $('<input name="connect" type="submit">').appendTo(this);
        this.submit(function(event) {
            event.preventDefault();
            callback($(this).find(':input[name=login]').val());
            return false;
        })
    },
    
    focus: function() {
        $(this).find(':input[name=login]').focus();
    }
});

var Client = Class({
    NOTIFICATION: _(['user_connect', 'user_disconnect']),
    tag: 'div',
    
    initialize: function() {
        this.askLogin();
    },
    
    askLogin: function() {
        this.loginForm = LoginForm.New(this.connect, this);
        this.append(this.loginForm);
    },

    buildInterface: function() {
        var children = [
            this.windowContainer = WindowContainer.New(this),
            this.userListContainer = UserListContainer.New(this),
            this.tabList = TabList.New(this),
            this.messageForm = MessageForm.New(this)
        ];
        $(this).empty();
        _.each(children, _.bind(function(c) { $(this).append(c) }, this));
        $('li#new-tab > button').focus();
    },
    
    connect: function(login) {
        if (login) {
            this.login = login;
            $.post(this.url('login'), { login: login }, this.subscribe);
        }
    },
    
    subscribe: function() {
        pushConnect(this.url(), this.dispatchPacket)
        this.buildInterface();
    },
    
    dispatchPacket: function(packet) {
        this['handle_' + packet.type](packet);
        if (this.NOTIFICATION.include(packet.type)) {
            this.windowContainer.appendNotification(packet);
        }
    },
    
    handle_hold_on: function(message) {
        
    },
    
    handle_message: function(message) {
        this.open(message.chan);
        this.windowContainer.appendMessage(message);
    },
    
    handle_user_connect: function(message) {
        var list = this.userListContainer.lists[message.chan];
        if (list) list.appendLogin(message.login);
    },

    handle_user_disconnect: function(message) {
        var list = this.userListContainer.lists[message.chan];
        if (list) list.removeLogin(message.login);
    },
    
    url: function(action) {
        return '/chat/' + (action || '');
    },

    switchTo: function(chan) {
        this.selectedChan = chan;
        if (chan) {
            this.messageForm.enable();
            _.invoke([this.tabList, this.userListContainer, this.windowContainer], 'select', chan);
        } else {
            this.messageForm.disable();
        }
        this.messageForm.focus();
    },
    
    open: function(chan) {
        if (!chan || _(this.tabList.tabs).chain().keys().include(chan).value()) return;
        _.invoke([this.tabList, this.userListContainer, this.windowContainer], 'append', chan);
    },
    
    join: function(chan) {
        if (!chan) return;
        this.open(chan);
        this.switchTo(chan);
        
        var list = this.userListContainer.lists[chan];
        var callback = _.bind(function(data, textStatus) {
            _(data.listeners).each(function(login) { list.appendLogin(login); });
        }, this);
        
        jQuery.post(this.url('join'), { chan: chan }, callback, 'json');
    },
    
    quit: function(chan) {
        jQuery.post(this.url('quit'), { chan: chan });
        _.invoke([this.tabList, this.userListContainer, this.windowContainer], 'remove', chan);
        if (_(this.tabList.tabs).isEmpty()) this.messageForm.disable();
    },
    
    send: function(chan, body, callback) {
        jQuery.post(this.url('send'), { body: body, chan: chan }, callback);
    }
    
});


jQuery(function(){
    var client = Client.New();
    $('body').append(client);
    client.loginForm.focus();
});