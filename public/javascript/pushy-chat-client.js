(jQuery(function(){
    var $ = jQuery;
    
    function newMessage(packet, status, fulldata, xhr) {
        $('body').append($('<p>').text(packet));
    }
    
    $.enableAjaxStream(true);
    function startStream(){
        $.get('/chat/foo', startStream, newMessage);
    }   
    startStream();

}));