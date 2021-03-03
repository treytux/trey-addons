odoo.define('website_sale_product_qty_limit.Limit_qty', function (require) {
    'use strict';
    require('web.dom_ready')
    let Class = require('web.Class')
    let Limit_qty = Class.extend({
        init: function() {
            let $product_id = $('input[name="product_id"]')
            let $variants_qty_limit = $('input[name="variants_qty_limit"]')
            let $quantity = $('.oe_website_spinner input[name="add_qty"]')
            if($variants_qty_limit.length > 0 && $quantity.length > 0 && $product_id.length > 0) {
                let variants_qty_limit_values = JSON.parse($variants_qty_limit.val())
                this.show_qty_limit($quantity, variants_qty_limit_values[$product_id.val()])
            }
        },
        show_qty_limit: function($quantity, qty_limit){
            if(qty_limit > 0) {
                let $qty_limit_msg = $('.js_wspql_qty_limit_msg')
                let $qty_limit_value = $('.js_wspql_qty_limit_value')
                if($qty_limit_msg.length > 0 && $qty_limit_value.length > 0) {
                    $qty_limit_msg.removeClass('d-none')
                    $qty_limit_value.text(qty_limit)
                }
            }
        }
    })
    let limit_qty = new Limit_qty()
    return {
        Limit_qty: Limit_qty,
        limit_qty: limit_qty,
    }
})
