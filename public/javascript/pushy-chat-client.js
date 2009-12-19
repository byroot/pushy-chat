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

var ChatWindow = Class({
    tag: 'div',
    
    initialize: function(parent, chan) {
        this.parent = parent;
        this.chan = chan;
        $(this).addClass('window').attr('id', 'window-' + chan);
        $(this).html('<h1>Hello world!</h1><h2>chan: ' + chan + '</h2>');
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
        this.messageList.append($('<li>').text(message.login + ': ' + message.body));
    }
    
});

var WindowContainer = Class({
    tag: 'div',
    
    initialize: function(chan) {
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
        this.parent = parent;
        this.window = chatWindow;
        $(this).append($('<a>').text(chatWindow.chan).click(chatWindow.activate.bind(chatWindow)));
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
    },
    
    appendTabFor: function(chatWindow) {
        this.append(Tab.New(this, chatWindow));       
    },
    
    
});

var MessageForm = Class({
    tag: 'div',
    
    initialize: function(parent) {
        $(this).attr('id', 'message-form');
        this.parent = parent;
        this.form = $('<form>');
        this.messageField = $('<input type="text" name="message">');
        this.append(this.form.append(this.messageField));
        this.form.submit(this.send.bind(this));
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
        this.append($('<p><input name="login" type="text"></p>'));
        this.append($('<p><input name="connect" type="submit"></p>'));
        this.submit(function(event) {
            event.preventDefault();
            callback($(this).find(':input[name=login]').val());
            return false;
        })
    }
});

var Client = Class({
    tag: 'body',
    
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
            $(this).append(this.windowContainer = WindowContainer.New());
            $(this).append(this.tabList = TabList.New(this.windowContainer));
            $(this).append(MessageForm.New(this));
            this.tabList.openTab('foo');
        }
    },
    
});


jQuery(function(){
    
    // // Send form
    //     var sendForm = $('form.send-form');
    //     sendForm.submit(function() {
    //         $.post($(this).attr('action'), $(this).serialize(), function() {
    //             $(this).find(':text').val('');
    //         }, 'text/plain');
    //         return false;
    //     })
    //     
    //     // Push client
    //     function newMessage(packet, status, fulldata, xhr) {
    //         $('body').append($('<p>').text(packet));
    //     }
    //     
    //     $.ajaxStop(function() { startStream('foo') });
    //     startStream('foo');
    //
    $('html').append(Client.New());
});