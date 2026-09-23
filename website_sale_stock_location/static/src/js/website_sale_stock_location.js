odoo.define('website_sale_stock_location.StockLocation', function (require) {
    'use strict';
    require('web.dom_ready')
    let Class = require('web.Class')
    let StockLocation = Class.extend({
        variant_stock_selector: '.js_wssl_variant_stock',
        out_of_stock_selector: '.js_wssl_out_of_stock',
        product_selector: 'input[name="product_id"]',
        init: function() {
            let self = this
            let $variant_stock = $(self.variant_stock_selector)
            if($variant_stock.length > 0) {
                self.show_location_stock()
            }
        },
        show_location_stock: function() {
            let self = this
            $(self.product_selector).change(function(){
                let $variant_stock = $(self.variant_stock_selector)
                let $current_variant_stock = $(self.variant_stock_selector + '[data-product_id="' + $(this).val() + '"]')
                let $out_of_stock = $(self.out_of_stock_selector)
                if($variant_stock.length > 0 && $current_variant_stock.length > 0 && $out_of_stock.length > 0) {
                    $variant_stock.addClass('d-none')
                    $out_of_stock.addClass('d-none')
                    if($current_variant_stock.find('.js_wssl_location_quantity_item').length > 0){
                        $current_variant_stock.removeClass('d-none')
                    } else {
                        $out_of_stock.removeClass('d-none')
                    }
                }
            })
        }
    })
    let stocklocation = new StockLocation()
    return {
        StockLocation: StockLocation,
        stocklocation: stocklocation,
    }
})
