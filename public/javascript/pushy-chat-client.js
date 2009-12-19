Function.prototype.bind = function() { // inspired by protoype
    var __method = this;
    var __args = jQuery.makeArray(arguments);
    var binding = __args.shift();
    return function() {
        return __method.apply(binding, __args.concat(jQuery.makeArray(arguments)));
    }
}

function class(klass) {
    
    klass.new = function() {
        var self = $.extend($('<' + klass.tag + '>'), klass)
        self.initialize.apply(self, arguments);
        return self;
    };
    
    return klass;
}

var ChatWindow = class({
    tag: 'div',
    
    initialize: function(parent, chan) {
        this.parent = parent;
        this.chan = chan;
        $(this).addClass('window').attr('id', 'window-' + chan);
        $(this).html('<h1>Hello world!</h1><p>chan: ' + chan + '</p>');
        $(this).hide();
    },
    
    activate: function() {
        console.log(this, 'activate');
        this.parent.setActiveWindow(this.chan);
    }
});

var WindowContainer = class({
    tag: 'div',
    
    initialize: function(chan) {
        $(this).attr('id', 'windowcontainer');
    },
    
    appendWindow: function(chan) {
        var newWindow = ChatWindow.new(this, chan);
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

var Tab = class({
    tag: 'li',
    
    initialize: function(parent, chatWindow) {
        this.parent = parent;
        this.window = chatWindow;
        $(this).append($('<a>').text(chatWindow.chan).click(chatWindow.activate.bind(chatWindow)));
    }
    
})

var TabList = class({
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
        this.append(Tab.new(this, chatWindow));       
    },
    
    
});

var MessageForm = class({
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
        console.log(arguments);
        jQuery.post('/chat/send/', {
            message: this.messageField.val(),
            chan: this.parent.windowContainer.activeWindow,
            login: this.parent.login
        }, this.clear.bind(this));
        return false;
    }
    
});

var LoginForm = class({
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

var Client = class({
    tag: 'body',
    
    initialize: function() {
        this.askLogin();
    },
    
    askLogin: function() {
        this.loginForm = LoginForm.new(this.connect.bind(this));
        this.append(this.loginForm);
    },
    
    connect: function(login){
        if (login) {
            this.login = login;
            $(this).empty();
            $(this).append(this.windowContainer = WindowContainer.new());
            $(this).append(this.tabList = TabList.new(this.windowContainer));
            $(this).append(MessageForm.new(this));
            this.tabList.openTab('foo');
        }
    },
    
});


jQuery(function(){
    var $ = jQuery;
    
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
    //     $.enableAjaxStream(true);
    //     function startStream(chan){
    //         $.get('/chat/' + chan, function(){}, newMessage);
    //     }
    //     $.ajaxStop(function() { startStream('foo') });
    //     startStream('foo');
    //
    $('html').append(Client.new());
});