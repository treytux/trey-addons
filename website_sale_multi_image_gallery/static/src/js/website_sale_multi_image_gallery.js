(function () {
    'use strict';
    var website = openerp.website;

    website.add_template_file('/website_sale_multi_image_gallery/static/src/xml/website_sale_multi_image_gallery.xml');
    website.website_sale_multi_image_gallery = {};

    website.website_sale_multi_image_gallery.Gallery = openerp.Widget.extend({
        template: 'website.website_sale_multi_image_gallery',
        init: function (parent, options) {
            this._super(parent);
        },
    });

    website.website_sale_multi_image_gallery.GalleryItem = openerp.Widget.extend({
        template: 'website.website_sale_multi_image_gallery_item',
        init: function (parent, options) {
            this.image_id = options.image_id;
            this.image_title = options.image_title;
            this._super(parent);
        },
    });

    website.website_sale_multi_image_gallery.GalleryAnchor = openerp.Widget.extend({
        template: 'website.website_sale_multi_image_gallery_anchor',
        init: function (parent, options) {
            this._super(parent);
        },
    });

    website.website_sale_multi_image_gallery.GalleryModal = openerp.Widget.extend({
        template: 'website.website_sale_multi_image_gallery_modal',
        dom_ready: $.Deferred(),
        ready: function(){
            return this.dom_ready.then(function() {}).promise();
        },
        init: function (parent, options) {
            this.dom_ready.resolve();

            var self = this;
            var product_images_input = $('input[name="product_images"]').val();
            var $image_span = $('span[itemprop="image"]');

            this.product_name = $('h1').text();
            this.product_images = {};
            if(typeof(product_images_input) != 'undefined'){
                this.product_images = JSON.parse(product_images_input);
            }

            $image_span.wrap('<a class="product_detail_a" title="' + this.product_name + '" data-gallery="data-gallery"></a>');

            $('.oe_website_sale').each(function () {
                var oe_website_sale = this;

                $(oe_website_sale).on('change', 'input.js_variant_change, select.js_variant_change, ul[data-attribute_value_ids]', function (ev) {
                    var $image_span = $('span[itemprop="image"]');
                    var $ul = $(this).parents('ul.js_add_cart_variants:first');
                    var $parent = $ul.closest('.js_product');
                    var $product_id = $parent.find('input.product_id').first();
                    if ($product_id.val()) {
                        self.add_items($product_id.val());
                    }
                });
            });
            this._super(parent);
        },
        add_items: function (product_id) {
            $('#blueimp-gallery-links').empty();
            if(typeof(product_id) != 'undefined' && product_id in this.product_images){
                var $anchor = $('a.product_detail_a');
                var $links = $('#blueimp-gallery-links');
                var $img = $('img.product_detail_img');
                $anchor.attr('style', 'visibility: hidden;');
                $links.attr('style', 'visibility: hidden;');
                $img.one('load', function() {
                    $anchor.attr('style', 'visibility: visible;');
                    $links.attr('style', 'visibility: visible;');
                }).each(function() {
                    if(this.complete) $(this).load();
                });
                var product_name = this.product_name;
                this.product_images[product_id].forEach(function(value, i) {
                    if(i == 0){
                        $anchor.attr('href', $img.attr('src'));
                    } else {
                        new website.website_sale_multi_image_gallery.GalleryItem(this, {image_id: value, image_title: product_name}).appendTo($links);
                    }
                });
            }
        },
    });

    website.ready().done(function () {
        website.if_dom_contains('#product_detail', function ($el) {
            var variants = $('form.js_add_cart_variants').attr('data-attribute_value_ids');
            if(typeof(variants) != 'undefined' && JSON.parse(variants).length > 0){
                var product_id = $('input.product_id').val();
                var website_sale_multi_image_gallery = new website.website_sale_multi_image_gallery.Gallery().insertAfter($('span[itemprop="image"]'));
                var website_sale_multi_image_gallery_modal = new website.website_sale_multi_image_gallery.GalleryModal();
                website_sale_multi_image_gallery_modal.appendTo($('body'));
                website_sale_multi_image_gallery_modal.add_items(product_id);
            }
        });
    });
}());
