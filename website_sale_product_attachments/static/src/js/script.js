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
                    $(this).on('change', 'input.js_variant_change, select.js_variant_change, ul[data-attribute_value_ids]', function (ev) {
                        self.show_attachments()
                    })
                })
            }
        },
        show_attachments: function() {
            var product_id = $('[name="product_id"]').val()
            var $attachments = $('.attachment-item-' + product_id.toString())
            $('.js_wspa_attachment').addClass('hidden')
            let $variants_attachments = $('.js_pa_variant_attachment')
            $variants_attachments.each(function(){
               $(this).addClass('hidden')
            })
            $attachments.removeClass('hidden')
        }
    })
    let attachments = new Attachments()
    return {
        Attachments: Attachments,
        attachments: attachments,
    }
})
