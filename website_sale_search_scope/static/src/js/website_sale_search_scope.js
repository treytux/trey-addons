(function() {
    'use strict';

    var _t = openerp._t;
    var website = openerp.website;

    website.ready().done(function() {
        website.if_dom_contains('.js_ss_category', function ($el) {
            var $buttons = $('.js_ss_category_btn');
            $buttons.on('click', function(e){
                e.preventDefault();
                var $form = $(this).closest('form');
                var $current = $('.js_ss_current_category');
                $current.text($(this).text());
                $form.attr('action', $(this).data('action'));
            });
        });
    });
}());
