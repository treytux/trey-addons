odoo.define('website_sale_products_pricelist.DiscountButtons', function (require) {
    'use strict'
    require('web.dom_ready')
    const core = require('web.core')
    const qweb = core.qweb
    const ajax = require('web.ajax')
    let Class = require('web.Class')
    let DiscountButtons = Class.extend({
        selector: '.oe_website_sale',
        events: {
            'click .js_wspp_add_qty_discount': '_onAddQty',
        },
        dom_ready: $.Deferred(),
        ready: function(){
            return this.dom_ready.then(function() {}).promise()
        },
        start: function () {
            this._updateDiscountTable()
            return this._super.apply(this, arguments)
        },
        init: function () {
            this.dom_ready.resolve()
            this._updateDiscountTable()
            let self = this
            $('.oe_website_sale').each(function () {
                var oe_website_sale = this
                $(oe_website_sale).on('change','input.js_variant_change, select.js_variant_change', function (ev) {
                    const $wrapper = $('div.js_wssp_qty_discounts')
                    $wrapper.addClass('d-none')
                    setTimeout(function () {
                        self._updateDiscountTable()
                    }, 500)
                })
            })
        },
        _onAddQty: function (ev) {
            const $btn = $(ev.currentTarget)
            const productId = parseInt($btn.data('product-id'))
            const qty = parseInt($btn.data('qty'))
            ajax.jsonRpc("/shop/cart/update_json", 'call', {
                product_id: productId,
                add_qty: qty,
                line_id: null,
                set_qty: false,
            }).then(function (data) {
                if (data && data.cart_quantity !== undefined) {
                    $(".my_cart_quantity").html(data.cart_quantity).hide().fadeIn(600)
                }
            })
        },
        _updateDiscountTable: function () {
            let self = this
            const $wrapper = $('div.js_wssp_qty_discounts')
            $wrapper.addClass('d-none')
            const $table = $('table.js_wssp_qty_discounts_table tbody')
            const $data = $('#variant_discount_data')
            if (!$table.length || !$data.length) return
            const discountData = JSON.parse($data.html())
            let variantId = $('input[name="product_id"]').val()
            let productId = $('input.product_template_id').val()
            let tiers = (discountData[productId] || {})[variantId] || []
            $table.empty()
            if (tiers.length === 0) {
                $wrapper.addClass('d-none')
            } else {
                tiers.forEach((line) => {
                    const [qty, price] = line.split('-')
                    const discountData = {
                        qty: qty,
                        price: price,
                        variantId: variantId,
                    }
                    const $row = qweb.render('website.wspp_table_row', discountData)
                    $table.append($row)
                })
                $('.js_wspp_add_qty_discount').on('click', function (ev) {
                    ev.preventDefault()
                    self._onAddQty(ev)
                })
                $wrapper.show()
                $wrapper.removeClass('d-none')
            }
        },
    })
    let discount_buttons = new DiscountButtons()
    return {
        DiscountButtons: DiscountButtons,
        discount_buttons: discount_buttons,
    }
})
