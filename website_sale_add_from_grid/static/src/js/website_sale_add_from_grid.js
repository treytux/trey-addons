(function () {
    'use strict'
    var website = openerp.website

    website.add_template_file('/website_sale_add_from_grid/static/src/xml/website_sale_add_from_grid.xml')
    website.website_sale_add_from_grid = {}

    website.website_sale_add_from_grid.Alert = openerp.Widget.extend({
        template: 'website.website_sale_add_from_grid_alert',
        init: function (parent, options) {
            this._super(parent)
        },
    })

    website.website_sale_add_from_grid.grid = openerp.Widget.extend({
        dom_ready: $.Deferred(),
        ready: function(){
            return this.dom_ready.then(function() {}).promise()
        },
        init: function (parent, options) {
            this._super(parent)
            var self = this
            let $spinners_minus = $('.js_wsafg_spinner_minus')
            let $spinners_plus = $('.js_wsafg_spinner_plus')
            $spinners_minus.each(function(){
                $(this).on('click', function(e){
                    e.preventDefault()
                    let $input = $(this).closest('.oe_website_spinner').find('input[name="product_qty"]')
                    if(parseInt($input.val()) > 0){
                        $input.val(parseInt($input.val()) - 1)
                        self.update_total($input)
                    }
                })
            })
            $spinners_plus.each(function(){
                $(this).on('click', function(e){
                    e.preventDefault()
                    let $input = $(this).closest('.oe_website_spinner').find('input[name="product_qty"]')
                    if(parseInt($input.val()) < parseInt($input.data('qty_available'))){
                        $input.val(parseInt($input.val()) + 1)
                        self.update_total($input)
                    }
                })
            })
            let $inputs = $('input.js_quantity')
            $inputs.each(function(){
                $(this).on('blur', function(){
                    self.check_stock(this)
                    self.update_total(this)
                })
            })
            let $btn_add = $('.js_wsafg_add')
            $btn_add.on('click', function(e){
                e.preventDefault()
                let products = []
                $inputs.each(function(){
                    let set_qty_value = parseInt($(this).val())
                    if(set_qty_value >= 0){
                        products.push([$(this).data('product_id'), null, null, set_qty_value])
                    }
                })
                if (products.length) {
                    openerp.jsonRpc('/shop/cart/update_json_multi', 'call', {
                        'products': products
                    }).then(function (data) {
                        let $cart_quantity = $('.my_cart_quantity')
                        if(data['cart_quantity'] != undefined){
                            $cart_quantity.text(data['cart_quantity'])
                            $cart_quantity.closest('li').removeClass('hidden')
                        } else {
                            $cart_quantity.text('')
                            $cart_quantity.closest('li').addClass('hidden')
                        }
                        let product_alert = new website.website_sale_add_from_grid.Alert()
                        product_alert.appendTo($('.oe_website_sale'))
                        let $product_alert = $('.js_wsafg_alert')
                        $cart_quantity.hide().delay(400).fadeIn(600)
                        $product_alert.delay(400).fadeIn(600).delay(2000).fadeOut(600)
                        location.reload()
                    })
                }
            })
        },
        update_total: function (input) {
            let $total = $(input).closest('tr').find('span.js_wsafg_total')
            let $price_total = parseFloat($(input).data('product_price') * parseInt($(input).val()))
            let $decimal_precision = $(input).data('currency_position')
            if ($(input).data('currency_position') === 'after') {
                $total.text(($price_total).toFixed(2) + ' ' + ($(input).data('currency_symbol') || ''))
            } else {
                $total.text(($(input).data('currency_symbol') || '') + ' ' + parseFloat($price_total).toFixed(2))
            }
        },
        check_stock: function (input) {
            if(!($(input).val()) || (parseInt($(input).val()) < 0)){
                $(input).val(0)
            }
            if(parseInt($(input).val()) > parseInt($(input).data('qty_available'))){
                $(input).val(parseInt($(input).data('qty_available')))
            }
        },
    })

    website.ready().done(function () {
        website.if_dom_contains('button.js_wsafg_add', function () {
            new website.website_sale_add_from_grid.grid()
        })
    })
}())
