odoo.define('website_sale_observations.observations', function (require) {
    'use strict'
    require('web.dom_ready')
    const ajax = require('web.ajax')
    const selector = 'textarea[name="web_order_observations"].js_wsobs_field'
    const $field = $(selector)
    if (!$field.length) {
        return
    }
    $field.on('change blur', function () {
        const value = $(this).val() || ''
        ajax.jsonRpc('/shop/cart/set_web_order_observations', 'call', {
            observations: value,
        })
    })
})
