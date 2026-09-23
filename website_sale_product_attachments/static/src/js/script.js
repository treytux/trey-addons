odoo.define('website_sale_product_attachments.Attachments', function (require) {
    'use strict';
    require('web.dom_ready')
    let Class = require('web.Class')
    let Attachments = Class.extend({
        attachments_selector: '.js_wspa_attachment',
        init: function() {
            let self = this
            let $attachments = $(self.attachments_selector)
            if($attachments.length > 0) {
                $('.oe_website_sale').each(function () {
                    $(this).on('change', 'input.js_variant_change, select.js_variant_change, ul[data-attribute_value_ids], input.product_id', function (ev) {
                        self.show_attachments()
                    })
                })
                self.show_attachments()
            }
        },
        show_attachments: function() {
            var product_id = $('.js_main_product input.product_id').val()
            if (!product_id) {
                return
            }
            var $attachments = $('.attachment-item-' + product_id.toString())
            $('.js_pa_variant_attachment_group').addClass('d-none')
            $attachments.removeClass('d-none')
        }
    })
    let attachments = new Attachments()
    return {
        Attachments: Attachments,
        attachments: attachments,
    }
})
