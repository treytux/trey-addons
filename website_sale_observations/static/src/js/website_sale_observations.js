odoo.define('website_sale_observations.note', function (require) {
    "use strict";

    require('web.dom_ready');
    var ajax = require('web.ajax');

    var $checkout_link = $('a[href$="/shop/checkout"]');
    var $note = $('textarea[name="note"]');
    if(!$checkout_link.length || !$note.length) {
        return $.Deferred().reject("DOM doesn't contain 'Order notes' or 'Checkout link'");
    }
    $checkout_link.on('click',function(e){
        e.preventDefault();
        ajax.jsonRpc('/shop/cart/note', 'call', {
            'note': $note.val()
        }).then(function (data) {
            window.location = $checkout_link.attr('href');
        });
    });
});
