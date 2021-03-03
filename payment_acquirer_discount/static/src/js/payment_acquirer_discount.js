odoo.define('payment_acquirer_discount.checkout', function (require) {
    'use strict'

    require('web.dom_ready')
    let ajax = require('web.ajax')
    let core = require('web.core')
    let _t = core._t
    let concurrency = require('web.concurrency')
    let dp = new concurrency.DropPrevious()

    let _onAcquirerUpdateAnswer = function(result) {
        console.log('_onAcquirerUpdateAnswer')
        console.log(result)
        let $discount = $('#order_discounted')
        if ($discount && result.new_amount_order_discounted) {
            $discount.find('.oe_currency_value').text(result.new_amount_order_discounted)
        }
        $('#order_delivery span.oe_currency_value').text(result.new_amount_delivery)
        $('#order_total_untaxed span.oe_currency_value').text(result.new_amount_untaxed)
        $('#order_total_taxes span.oe_currency_value').text(result.new_amount_tax)
        $('#order_total span.oe_currency_value').text(result.new_amount_total)
    }
    let _onAcquirerClick = function(ev) {
        let values = {'acquirer_id': $(this).data('acquirer-id')}
        dp.add(ajax.jsonRpc('/shop/update_acquirer', 'call', values))
          .then(_onAcquirerUpdateAnswer)
    }
    let $acquirers = $("form.o_payment_form input[type='radio']")
    $acquirers.click(_onAcquirerClick)
})
