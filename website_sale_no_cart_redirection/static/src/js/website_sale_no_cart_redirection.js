(function() {
    'use strict'
    let website = openerp.website
    let core = require('web.core');
    let _t = core._t;
    website.ready().done(function() {
        let add_cart_button = 'a.js_wsncr_button'
        website.if_dom_contains(add_cart_button, function() {
            let $add_cart_buttons = $(add_cart_button)
            $add_cart_buttons.each(function(){
                $(this).on('click', function(ev) {
                    ev.preventDefault()
                    let $product_price = $(this).closest('div.product_price')
                    let $input = $product_price.find('input')
                    if($input.length > 0) {
                        openerp.jsonRpc('/shop/cart/update_json', 'call', {
                            'line_id': null,
                            'product_id': parseInt($input.val(), 10),
                            'add_qty': 1
                        }).then(function (data) {
                            if (!data.quantity) {
                                location.reload()
                                return
                            }
                            let $my_crt_qty = $('.my_cart_quantity')
                            if($my_crt_qty.length > 0) {
                                $my_crt_qty.closest('li.hidden').removeClass('hidden', !data.quantity)
                                $my_crt_qty.html(data.cart_quantity).hide().fadeIn(600, function(){
                                    alert(_t('Product added to cart.'))
                                })
                            }
                            let $cart_total = $('#cart_total')
                            if($cart_total.length > 0) {
                               $cart_total.replaceWith(data['website_sale.total'])
                            }
                        })
                    }
                    return false
                })
            })
        })
    })
})()
