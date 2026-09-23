odoo.define('website_sale_reference.client_order_ref', function (require) {
    'use strict'
    require('web.dom_ready')
    const ajax = require('web.ajax')
    const selector = 'textarea[name="client_order_ref"].js_wsref_field'
    const $field = $(selector)
    if (!$field.length) {
        return
    }
    $field.on('change blur', function () {
        const value = $(this).val() || ''
        ajax.jsonRpc('/shop/cart/set_client_order_ref', 'call', {
            client_order_ref: value,
        })
    })
})
