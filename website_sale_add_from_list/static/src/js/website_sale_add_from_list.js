(function () {
    'use strict'
    var website = openerp.website

    website.add_template_file('/website_sale_add_from_list/static/src/xml/website_sale_add_from_list.xml')
    website.website_sale_add_from_list = {}

    website.website_sale_add_from_list.ModalVariant = openerp.Widget.extend({
        template: 'website.website_sale_add_from_list_variant',
        init: function (parent, options) {
            this.id = options.product_id
            this.name = options.product_name
            this.qty_available = options.product_qty_available
            this.lst_price = options.product_lst_price
            this._super(parent)
        },
    })

    website.website_sale_add_from_list.ModalAlert = openerp.Widget.extend({
        template: 'website.website_sale_add_from_list_alert',
        init: function (parent, options) {
            this._super(parent)
        },
    })

    website.website_sale_add_from_list.Modal = openerp.Widget.extend({
        template: 'website.website_sale_add_from_list_modal',
        dom_ready: $.Deferred(),
        ready: function(){
            return this.dom_ready.then(function() {}).promise()
        },
        init: function (parent, options) {
            this.dom_ready.resolve()
            var self = this
            self.$product = options.product
            this._super(parent)
        },
        setup: function () {
            var self = this
            self.appendTo($('body'))
            self.$modal = $('#wsafl_modal')
            let $modal_title = self.$modal.find('.modal-title')
            $modal_title.text(self.$product.data('product_name'))
        },
        check_stock: function (input) {
            if(parseInt($(input).val()) < 0){
                $(input).val(0)
            }
            if(parseInt($(input).val()) > parseInt($(input).data('qty_available'))){
                $(input).val(parseInt($(input).data('qty_available')))
            }
        },
        update_total: function (input) {
            let $total = $(input).closest('tr').find('span.js_wsafl_total')
            let $price_total = parseFloat($(input).data('product_price') * parseInt($(input).val()))
            let $decimal_precision = $(input).data('currency_position')
            if ($(input).data('currency_position') === 'after') {
                $total.text(($price_total).toFixed(2) + ' ' + ($(input).data('currency_symbol') || ''))
            } else {
                $total.text(($(input).data('currency_symbol') || '') + ' ' + parseFloat($price_total).toFixed(2))
            }
        },
        show: function (parent, options) {
            let $product_modal = $('#wsafl_modal')
            $product_modal.modal('show')
        },
        create_variants: function (data) {
            var self = this
            let $tbody = self.$modal.find('.modal-body tbody')
            $tbody.append(data)
            let $spinners_minus = self.$modal.find('.js_wsafl_spinner_minus')
            let $spinners_plus = self.$modal.find('.js_wsafl_spinner_plus')
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
            let $inputs = self.$modal.find('input')
            $inputs.each(function(){
                $(this).on('blur', function(){
                    self.check_stock(this)
                    self.update_total(this)
                })
            })
            let $btn_add = self.$modal.find('.js_wsafl_add')
            $btn_add.on('click', function(e){
                e.preventDefault()
                let products = []
                let $inputs = self.$modal.find('input')
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
                        let $btn_close = self.$modal.find('.js_wsafl_close')
                        $btn_close.trigger('click')
                        let $cart_quantity = $('.my_cart_quantity')
                        if(data['cart_quantity'] != undefined){
                            $cart_quantity.text(data['cart_quantity'])
                            $cart_quantity.closest('li').removeClass('hidden')
                        } else {
                            $cart_quantity.text('')
                            $cart_quantity.closest('li').addClass('hidden')
                        }
                        let product_alert = new website.website_sale_add_from_list.ModalAlert()
                        product_alert.appendTo($('.oe_website_sale'))
                        let $product_alert = $('.js_wsafl_alert')
                        $cart_quantity.hide().delay(400).fadeIn(600);
                        $product_alert.delay(400).fadeIn(600).delay(2000).fadeOut(600)
                        location.reload()
                    })
                }
            })
        },
    })

    website.ready().done(function () {
        let $show_modal_btn = $('.js_wsafl_show_modal_btn')
        if($show_modal_btn.length > 0) {
            $show_modal_btn.on('click', function(e){
                e.preventDefault()
                let $product_modal = $('#wsafl_modal')
                $product_modal.remove()
                let $product_alert = $('.js_wsafl_alert')
                $product_alert.remove()
                let product_modal = new website.website_sale_add_from_list.Modal(this, {product: $(this)})
                product_modal.setup()
                $.get('/shop/get_product_variants', {
                    'product_id': $(this).data('product_id')
                }).then(function (data) {
                    product_modal.create_variants(data)
                    product_modal.show()
                    $('body').trigger('wsafl_on_modal_show', [$('#wsafl_modal')])
                })
            })
        }
    })
}())
