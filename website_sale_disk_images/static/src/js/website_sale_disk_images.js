(function () {
    'use strict';
    $(document).ready(function () {
        function gallery(product_id, sizes, callback) {
            console.debug("LOADING GALLERY. Product", product_id);

            openerp.jsonRpc('/shop/product/image-disk', 'call', {
                'product_id': product_id,
                'sizes': sizes
            }).then(function(result) {
                callback(result);
            });
        }

        function print_gallery(result) {
            console.debug("RESULT", result);

            var images = result['images'];
            var nombre_producto = result['product'];

            $('.images_gallery').html('');
            if (images.length > 0) {
                $.each(images, function(i, item) {
                    // console.debug(item);
                    $('.images_gallery').append(
                        '<a href="' + item['original'] + '" title="' + nombre_producto + '" data-gallery="data-gallery">' +
                            '<img src="' + item['50x50'] + '" alt="' + nombre_producto + '">' +
                        '</a>'
                    );
                });
                $('.big_gallery').attr('src', images[0]['400x350']);
                $('.gallery_help_not_found').addClass('hidden');
            } else {
                $('.big_gallery').attr('src', '/website_sale_disk_images/static/src/img/not-found.png');
                console.debug($('.big_gallery').attr('src'));
                if (result['name']) {
                    $('.gallery_help_not_found').removeClass('hidden');
                    $('.gallery_help_not_found').find('.name').html(result['name']);
                    $('.gallery_help_not_found').find('.path').html(result['path']);
                    // console.debug($('.gallery_help_not_found').find('.name'));
                }
            }
        }

        $('.oe_website_sale').each(function () {
            var oe_website_sale = this;

            $(oe_website_sale).on('change', 'input.js_variant_change, select.js_variant_change', function (ev) {
                var $ul = $(this).parents('ul.js_add_cart_variants:first');
                var $parent = $ul.closest('.js_product');
                var $product_id = $parent.find('input.product_id').first();

                if ($product_id.val()) {
                    gallery($product_id.val(), [[50, 50], [400, 350]], print_gallery);
                } else {
                    console.debug("no hay product id");
                }
            });
        });

        // comprobamos si hay imagenes sin foto en disco
        var img_not_found = $('*[data-gallery-not_found-path]');
        if (img_not_found.length > 0) {
            $('#products_grid').prepend(
                '<div id="products_gallery_not_found" class="alert alert-warning" role="alert">' +
                    '<button type="button" class="close" data-dismiss="alert">' +
                        '<span aria-hidden="true">&times;</span><span class="sr-only">Close</span>' +
                    '</button>' +
                '<div>'
            );

            var $alert = $('#products_gallery_not_found');
            $alert.append('<p>Sube las siguientes fotos al path:<br/> ' + $(img_not_found[0]).data('gallery-not_found-path') + '</p><br/>');

            $.each(img_not_found, function(i, item) {
                $alert.append('<p>' + $(item).data('gallery-not_found-name') + '</p>');
            });
        }
        console.debug(img_not_found.length);
    });
})();
