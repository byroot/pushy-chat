
function pushConnect(url, callback) {
    jQuery.enableAjaxStream(true);
    function startStream(){
        var recursive = _.bind(setTimeout, window, startStream, 20);
        jQuery.get(url, recursive, callback);
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
        $(this).append($('<span>').addClass('login').text('<' + login + '> '))
        $(this).append($('<span>').addClass('message-body').text(body))
    }
});

var ChatWindow = Class({
    tag: 'div',
    
    initialize: function(parent, chan) {
        this.parent = parent;
        this.chan = chan;
        $(this).addClass('window').attr('id', 'window-' + chan);
        this.messageList = $('<ul>').addClass('message-list').appendTo(this);
    },
    
    appendMessage: function(message) {
        this.messageList.append(Message.New(message.login, message.body));
    }
    
});

var WindowContainer = Class({
    tag: 'div',
    
    initialize: function(parent) {
        this.windows = {};
        $(this).parent = parent;
        $(this).attr('id', 'windowcontainer');
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
    
    select: function(chan) {
        this.activeWindow = this.windows[chan];
        $('#windowcontainer > .window').hide();
        $('#windowcontainer > #window-' + chan).show();
    }
    
});

var UserList = Class({
    tag: 'ul',
    
    initialize: function(parent, chan) {
        this.attr('id', 'user-list-' + chan).addClass('user-list');
        this.parent = parent;
        this.chan = chan;
    },
    
    appendLogin: function(login) {
        $('<li>').attr('id', 'login-' + login).text(login).appendTo(this);
    },
    
    removeLogin: function(login) {
        $(this).find('#login-' + login).remove();
    }
    
});

var UserListContainer = Class({
    tag: 'div',
    
    initialize: function(parent) {
        this.attr('id', 'user-list-container');
        this.parent = parent;
        this.lists = {};
    },
    
    append: function(chan) {
        $(this).append(this.lists[chan] = UserList.New(this, chan));
        return this.lists[chan];
    },
    
    remove: function(chan) {
        $(this).find('#user-list-chan').remove();
    },
    
    select: function(chan) {
        this.activeList = this.lists[chan];
        $('#user-list-container > .user-list').hide();
        $('#user-list-container > #user-list-' + chan).show();
    }
    
});

var Tab = Class({
    tag: 'li',
    
    initialize: function(parent, chan) {
        this.attr('id', 'tab-' + chan).addClass('tab');
        this.chan = chan;
        this.parent = parent;
        $(this).append($('<a>').text(chan));
        $(this).click(this.activate);
    },
    
    activate: function() {
        this.parent.parent.switchTo(this.chan);
    }
})

var TabList = Class({
    tag: 'ul',
    
    initialize: function(parent) {
        $(this).attr('id', 'tablist');
        this.parent = parent;
        this.tabs = {};
        this.newTabAction = $('<li><a>New tab</a></li>').click(this.askChanName).appendTo(this);
    },
    
    askChanName: function(event) {
        this.parent.join(window.prompt('Chan name'));
    },
    
    append: function(chan) {
        $(this).append(this.tabs[chan] = Tab.New(this, chan));
        return this.tabs[chan];
    },
    
    remove: function(chan) {
        $(this).find('#tab-' + chan).remove();
    },
    
    select: function(chan) {
        $('#tablist > .tab').removeClass('selected');
        $('#tablist > #tab-' + chan).addClass('selected');        
    }
    
});

var MessageForm = Class({
    tag: 'div',
    
    initialize: function(parent) {
        $(this).attr('id', 'message-form');
        this.parent = parent;
        this.form = $('<form>').submit(this.send);
        this.messageField = $('<input id="message" type="text" name="message">').appendTo(this.form);
        $('<input type="submit">').appendTo(this.form)
        this.form.appendTo(this);
    },
    
    clear: function(){
        this.messageField.val('');
    },
    
    send: function(event) {
        event.preventDefault();
        this.parent.send(
            this.parent.selectedChan,
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
    }
});

var Client = Class({
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
        $(this).empty()
        _.each(children, _.bind(function(c) { $(this).append(c) }, this));
    },
    
    connect: function(login){
        if (login) {
            this.login = login;
            pushConnect(this.url(), this.parsePackets)           
            this.buildInterface();
            this.join('master');
        }
    },
    
    parsePackets: function(packet, status, fulldata, xhr) {
        try{
            packet = eval(packet);            
            if (packet && packet.messages) {
                _(packet.messages).each(_.bind(function(message) {
                    this['handle_' + message.type](message);
                }, this));
            }
        } catch(e) {
            console.log('invalid packet: ', packet);            
        }
    },
    
    handle_message: function(message) {
        this.windowContainer.appendMessage(message);
    },
    
    handle_user_connect: function(message) {
        console.log('handle_user_connect', message);
        this.userListContainer.lists[message.chan].appendLogin(message.login);
    },

    handle_user_disconnect: function(message) {
        console.log('handle_user_disconnect', message);
        this.userListContainer.lists[message.chan].removeLogin(message.login);
    },
    
    url: function(action) {
        return '/chat/' + (action || '') + '?login=' + this.login;
    },

    switchTo: function(chan) {
        this.selectedChan = chan;
        _.invoke([this.tabList, this.userListContainer, this.windowContainer], 'select', chan);
    },
    
    join: function(chan) {
        _.invoke([this.tabList, this.userListContainer, this.windowContainer], 'append', chan);
        this.switchTo(chan);
        
        var list = this.userListContainer.lists[chan];
        var callback = _.bind(function(data, textStatus) {
            _(data.listeners).each(function(login) { list.appendLogin(login); });
        }, this);
        
        jQuery.post(this.url('join'), { chan: chan }, callback, 'json');
    },
    
    quit: function(chan) {
        jQuery.post(this.url(quit), { chan: chan });
        _.invoke([this.tabList, this.userListContainer, this.windowContainer], 'remove', chan);
    },
    
    send: function(chan, body, callback) {
        jQuery.post(this.url('send'), { body: body, chan: chan }, callback);
    }
    
});


jQuery(function(){
    $('body').append(Client.New());
});