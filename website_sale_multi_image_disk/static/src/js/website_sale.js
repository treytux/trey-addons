odoo.define('website_sale_multi_image_disk.website_sale', function (require) {
    "use strict"
    require("website_sale.website_sale")

    let update_product_image = function(oe_website_sale, el) {
        console.log('update_product_image')
        // var $img;
        // if ($('#o-carousel-product').length) {
        //     $img = $(event_source).closest('tr.js_product, .oe_website_sale').find('img.js_variant_img');
        //     $img.attr("src", "/web/image/product.product/" + product_id + "/image");
        //     $img.parent().attr('data-oe-model', 'product.product').attr('data-oe-id', product_id)
        //         .data('oe-model', 'product.product').data('oe-id', product_id);

        //     var $thumbnail = $(event_source).closest('tr.js_product, .oe_website_sale').find('img.js_variant_img_small');
        //     if ($thumbnail.length !== 0) { // if only one, thumbnails are not displayed
        //         $thumbnail.attr("src", "/web/image/product.product/" + product_id + "/image/90x90");
        //         $('.carousel').carousel(0);
        //     }
        // }
        // else {
        //     $img = $(event_source).closest('tr.js_product, .oe_website_sale').find('span[data-oe-model^="product."][data-oe-type="image"] img:first, img.product_detail_img');
        //     $img.attr("src", "/web/image/product.product/" + product_id + "/image");
        //     $img.parent().attr('data-oe-model', 'product.product').attr('data-oe-id', product_id)
        //         .data('oe-model', 'product.product').data('oe-id', product_id);
        // }
        // // reset zooming constructs
        // $img.filter('[data-zoom-image]').attr('data-zoom-image', $img.attr('src'));
        // if ($img.data('zoomOdoo') !== undefined) {
        //     $img.data('zoomOdoo').isReady = false;
        // }

    }

    $('.oe_website_sale').each(function () {
        var oe_website_sale = this
        $(oe_website_sale).on('change', 'input.js_product_change', function () {
            console.log('change', 'input.js_product_change')
            update_product_image(oe_website_sale, this)
            // var self = this;
            // var $parent = $(this).closest('.js_product');
            // $.when(base.ready()).then(function() {
            //     $parent.find(".oe_default_price:first .oe_currency_value").html( price_to_str(+$(self).data('lst_price')) );
            //     $parent.find(".oe_price:first .oe_currency_value").html(price_to_str(+$(self).data('price')) );
            // });
            // update_product_image(this, +$(this).val());
        })
        $(oe_website_sale).on('change', 'input.js_variant_change, select.js_variant_change, ul[data-attribute_value_ids]', function (ev) {
            console.log('change', 'input.js_variant_change, select.js_variant_change, ul[data-attribute_value_ids]')
            update_product_image(oe_website_sale, this)
        })

    })
});
