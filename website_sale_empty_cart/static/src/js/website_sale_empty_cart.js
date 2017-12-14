(function () {
    'use strict';
    var website = openerp.website,
        _t = openerp._t

    website.website_sale_clean_shopping_cart = {};

    website.website_sale_clean_shopping_cart.Cart = openerp.Widget.extend({
        dom_ready: $.Deferred(),
        ready: function(){
            return this.dom_ready.then(function() {}).promise();
        },
        init: function (parent, options) {
            this._super(parent);
            var self = this,
                remove_cart_item = $('.js_wscsc_remove_cart_item'),
                empty_cart_button = $('.js_wscsc_empty_cart');

            remove_cart_item.on('click', function (e) {
                e.preventDefault();
                var cart_line_row = $(this).parent().parent().closest('tr'),
                    cart_line_input = cart_line_row.find('input.js_quantity.form-control');
                cart_line_input.val(0);
                cart_line_input.change();
                setTimeout(function() {
                    cart_line_row.addClass('fade');
                }, 1000);
            });

            empty_cart_button.on('click', function (e) {
                e.preventDefault();
                openerp.jsonRpc(
                    '/shop/empty-cart', 'call', {
                    }).then(function () {
                        window.location.reload();
                    });
            });
        },

    });

    website.ready().done(function () {
        website.if_dom_contains(['.fa fa-long-arrow-left', '.js_add_cart_json'], function ($el) {
            new website.website_sale_clean_shopping_cart.Cart();
        });
    });
}());

