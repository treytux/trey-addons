odoo.define('website_sale_checkout_skip_payment_terms.terms_and_conditions', function (require) {
    'use strict'
    require('web.dom_ready')
    const Class = require('web.Class')
    const TermsAndConditions = Class.extend({
        dom_ready: $.Deferred(),
        ready: function(){
            return this.dom_ready.then(function() {}).promise()
        },
        init: function () {
            this.dom_ready.resolve()
            let self = this
            let checkbox_tc_selector = '#checkbox_tc'
            let $checkbox_tc = $(checkbox_tc_selector)
            let submit_btn_selector = '.js_skip_payment .a-submit'
            let $submit_btn = $(submit_btn_selector)
            if (
                $submit_btn.length
                && $checkbox_tc.length
            ) {
                $checkbox_tc.on('click', function (e) {
                    if ($(this).is(':checked')) {
                        $submit_btn.removeClass('disabled')
                        $submit_btn.attr('aria-disabled', 'false')
                    } else {
                        $submit_btn.addClass('disabled')
                        $submit_btn.attr('aria-disabled', 'true')
                    }
                })
            } else if ($submit_btn.length) {
                $submit_btn.removeClass('disabled')
                $submit_btn.attr('aria-disabled', 'false')
            }
        },
    })
    const termsAndConditions = new TermsAndConditions()
    return {
        TermsAndConditions,
        termsAndConditions,
    }
})
