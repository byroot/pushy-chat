var app = (jQuery(function(){
    var $ = jQuery;
    
    $.ajax({
        type: 'GET',
        url: '/chat/foo',
        dataType: 'text',
        dataFilter: function(data, type) {
            document.write(data);
            return data;
        },
        timeout: 20000
    })
}));