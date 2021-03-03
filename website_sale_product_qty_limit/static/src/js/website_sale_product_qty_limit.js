$(document).ready(function() {
    'use strict';
    var website = openerp.website

    let show_qty_limit = function($quantity, qty_limit){
        if(qty_limit > 0) {
            let $qty_limit_msg = $('.js_wspql_qty_limit_msg')
            let $qty_limit_value = $('.js_wspql_qty_limit_value')
            if($qty_limit_msg.length > 0 && $qty_limit_value.length > 0) {
                $qty_limit_msg.removeClass('hidden')
                $qty_limit_value.text(qty_limit)
            }
        }
    }

    website.ready().done(function() {
        let $product_id = $('.js_add_cart_variants input[name="product_id"]')
        let $variants_qty_limit = $('input[name="variants_qty_limit"]')
        let $quantity = $('.oe_website_spinner input.js_quantity')
        if($variants_qty_limit.length > 0 && $quantity.length > 0 && $product_id.length > 0) {
            let variants_qty_limit_values = JSON.parse($variants_qty_limit.val())
            show_qty_limit($quantity, variants_qty_limit_values[$product_id.val()])
        }
    })
})
