(function() {
    'use strict';
    var website = openerp.website;
    website.ready().done(function () {
        website.if_dom_contains('.js_pa_variant_attachment', function ($el) {
            function show_attachments() {
                var product_id = $('[name="product_id"]').val();
                var $attachments = $('.attachment-item-' + product_id.toString());
                $('.js_pa_variant_attachment').addClass('hidden');
                $attachments.removeClass('hidden');
            }
            $('.oe_website_sale').each(function () {
                var oe_website_sale = this;
                $(oe_website_sale).on('change', 'input.js_variant_change, select.js_variant_change, ul[data-attribute_value_ids]', function (ev) {
                    show_attachments()
                });
            });
        });
    });
}());
