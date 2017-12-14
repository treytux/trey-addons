(function () {
    'use strict';
    var website = openerp.website;
    var _t = openerp._t;
    openerp.website.ready().done(function() {
        $('[data-toggle="tooltip"]').tooltip();
        $('.js_wmpi_send_message').each(function(){
            $(this).on('click', function (event){
                event.preventDefault();
                $(".js_wmpi_message_form").removeClass('hidden');
                $('.js_wmpi_send_message').addClass('hidden');
            });
        });

    });
})();
