(function () {
    'use strict';
    var website = openerp.website;

    website.add_template_file('/website_sale_multi_image_zoom/static/src/xml/website_sale_multi_image_zoom.xml');
    website.website_sale_multi_image_zoom = {};

    website.website_sale_multi_image_zoom.Zoom = openerp.Widget.extend({
        dom_ready: $.Deferred(),
        ready: function(){
            return this.dom_ready.then(function() {}).promise();
        },
        init: function (parent, options) {
            this.dom_ready.resolve();

            var self = this;
            var $image = $('span[itemprop="image"]');
            var zoom_options = $image.data('zoom');
            $image.wrapInner('<span class="js_miz_zoom"></div>');
            var $zoom = $('span.js_miz_zoom');
            $zoom.zoom({ on: zoom_options });
            this._super(parent);
        },
    });

    website.website_sale_multi_image_zoom.ZoomGallery = openerp.Widget.extend({
        template: 'website.website_sale_multi_image_zoom_gallery',
        dom_ready: $.Deferred(),
        ready: function(){
            return this.dom_ready.then(function() {}).promise();
        },
        init: function (parent, options) {
            this.dom_ready.resolve();

            var self = this;
            var product_images_input = $('input[name="product_images"]').val();
            this.product_images = {};
            if(typeof(product_images_input) != 'undefined'){
                this.product_images = JSON.parse(product_images_input);
            }
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
            var $links = $('.js_miz_gallery');
            $links.empty();
            $('.js_miz_zoom img').attr('src', '');
            if(typeof(product_id) != 'undefined' && product_id in this.product_images){
                var $anchor = $('a.product_detail_a');
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
                    new website.website_sale_multi_image_zoom.ZoomGalleryItem(this, {image_id: value, image_title: product_name}).appendTo($links);
                });
                var $items = $('.js_miz_gallery_item');
                if($items.length > 0){
                    $items.each(function(){
                        $(this).on('click', function(e){
                            e.preventDefault();
                            $('.js_miz_zoom img').attr('src', $(this).attr('href'));
                        });
                    });
                    $items[0].click();
                }
            }
        },
    });

    website.website_sale_multi_image_zoom.ZoomGalleryItem = openerp.Widget.extend({
        template: 'website.website_sale_multi_image_zoom_gallery_item',
        init: function (parent, options) {
            this.image_id = options.image_id;
            this.image_title = options.image_title;
            this._super(parent);
        },
    });

    website.ready().done(function () {
        website.if_dom_contains('#product_detail', function ($el) {
            var product_id = $('input.product_id').val();
            var website_sale_multi_image_zoom = new website.website_sale_multi_image_zoom.Zoom();
            var website_sale_multi_image_zoom_gallery = new website.website_sale_multi_image_zoom.ZoomGallery();
            website_sale_multi_image_zoom_gallery.appendTo($('span[itemprop="image"]'));
            website_sale_multi_image_zoom_gallery.add_items(product_id);
        });
    });
}());
