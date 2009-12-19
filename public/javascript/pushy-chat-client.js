var $ = jQuery;

Function.prototype.bind = function() { // inspired by protoype
    var __method = this;
    var __args = jQuery.makeArray(arguments);
    var binding = __args.shift();
    return function() {
        return __method.apply(binding, __args.concat(jQuery.makeArray(arguments)));
    }
}

function Class(klass) {
    
    klass.New = function() {
        var self = $.extend($('<' + klass.tag + '>'), klass)
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
        this.messageList = $('<ul>').addClass('message-list');
        $(this).append(this.messageList);
        $(this).hide();
        this.connect();
    },
    
    activate: function() {
        this.parent.setActiveWindow(this.chan);
    },
    
    connect: function() {
        var callback = this.parsePackets.bind(this);
        var chan = this.chan;
        jQuery.enableAjaxStream(true);
        function startStream(){
            jQuery.get('/chat/' + chan, 
                function(){ setTimeout(startStream, 20)}, 
                callback
            );
        }
        startStream();
    },
    
    parsePackets: function(packet, status, fulldata, xhr) {
        var message = eval(packet);
        if (message) this.appendMessage(message);
    },
    
    appendMessage: function(message) {
        this.messageList.append(Message.New(message.login, message.body));
    }
    
});

var WindowContainer = Class({
    tag: 'div',
    
    initialize: function(parent) {
        $(this).parent = parent;
        $(this).attr('id', 'windowcontainer');
    },
    
    appendWindow: function(chan) {
        var newWindow = ChatWindow.New(this, chan);
        $(this).append(newWindow);
        this.setActiveWindow(chan);
        return newWindow;
    },
    
    setActiveWindow: function(chan) {
        this.activeWindow = chan;
        $('#windowcontainer > .window').hide();
        $('#windowcontainer > #window-' + chan).show();
    }
    
});

var Tab = Class({
    tag: 'li',
    
    initialize: function(parent, chatWindow) {
        this.chan = chatWindow.chan;
        this.attr('id', 'tab-' + this.  chan).addClass('tab');
        this.parent = parent;
        this.window = chatWindow;
        window.tab = this;
        $('<a>').text(chatWindow.chan).appendTo(this);
        $(this).click(this.activate.bind(this));
    },
    
    activate: function() {
        this.window.activate();
        this.parent.setActiveTab(this.chan);
    }
})

var TabList = Class({
    tag: 'ul',
    
    initialize: function(container) {
        this.container = container;
        $(this).attr('id', 'tablist');
        this.openTab('master')
    },
    
    openTab: function(chan) {
        var newWindow = this.container.appendWindow(chan);
        this.appendTabFor(newWindow);
        this.setActiveTab(chan);
    },
    
    appendTabFor: function(chatWindow) {
        this.append(Tab.New(this, chatWindow));       
    },
    
    setActiveTab: function(chan) {
        this.activeTab = chan;
        $('#tablist > .tab').removeClass('selected');
        $('#tablist > #tab-' + chan).addClass('selected');        
    }
    
});

var MessageForm = Class({
    tag: 'div',
    
    initialize: function(parent) {
        $(this).attr('id', 'message-form');
        this.parent = parent;
        this.form = $('<form>');
        this.messageField = $('<input id="message" type="text" name="message">').appendTo(this.form);
        $('<input type="submit">').appendTo(this.form)
        this.form.submit(this.send.bind(this));
        this.form.appendTo(this);
    },
    
    clear: function(){
        this.messageField.val('');
    },
    
    send: function(event) {
        event.preventDefault();
        jQuery.post('/chat/send/', {
            message: this.messageField.val(),
            chan: this.parent.windowContainer.activeWindow,
            login: this.parent.login
        }, this.clear.bind(this));
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
        this.loginForm = LoginForm.New(this.connect.bind(this));
        this.append(this.loginForm);
    },
    
    connect: function(login){
        if (login) {
            this.login = login;
            $(this).empty();
            $(this).append(this.windowContainer = WindowContainer.New(this));
            $(this).append(this.tabList = TabList.New(this.windowContainer));
            $(this).append(MessageForm.New(this));
            this.tabList.openTab('foo');
        }
    },
    
});


jQuery(function(){
    $('body').append(Client.New());
});