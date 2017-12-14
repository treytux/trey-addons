(function () {
    'use strict';
    $(document).ready(function () {
        function gallery(product_id, size_small, size_big, callback) {
            //console.debug("LOADING GALLERY. Product", product_id);
            openerp.jsonRpc('/images/xhr/product/' + product_id, 'call', {})
                .then(function(result) {
                    callback(result, size_small, size_big);
                }
            );
        }

        function gallery_tmpl(product_id, size_small, size_big, callback) {
            //console.debug("LOADING GALLERY. Product", product_id);
            openerp.jsonRpc('/images/xhr/tmpl/' + product_id, 'call', {})
                .then(function(result) {
                    callback(result, size_small, size_big);
                }
            );
        }

        function print_gallery(result, size_small, size_big) {

            var images = result;
            var nombre_producto = result['product'];

            $('.product-gallery').html('');

            if (images.length > 0) {
                $.each(images, function(i, item) {
                    $('.product-image').html(
                        '<a href="/images/' + item + '" title="' + item + '" data-gallery="data-gallery" class="product-image-default">' +
                            '<img src="/images/400x400/' + item + '" alt="' + item + '" class="img img-responsive product_detail_img_gallery">' +
                        '</a>'
                    );
                    if(i > 0) {
                        $('.product-gallery').append(
                            '<a href="/images/' + item + '" title="' + item + '" data-gallery="data-gallery">' +
                                '<img src="/images/200x200/' + item + '" alt="' + item + '" class="img img-responsive">' +
                            '</a>'
                        );
                    }
                });
            } else {
                $('.product-image').html(
                    '<a href="" title="" data-gallery="data-gallery" class="product-image-default">' +
                        '<img src="/web/static/src/img/placeholder.png" alt="" class="img img-responsive product_detail_img_gallery">' +
                    '</a>'
                );
            }
        }

        // evento cuando se cambia una variante
        $('.oe_website_sale').each(function () {
            var oe_website_sale = this;

            $(oe_website_sale).on('change', 'input.js_variant_change, select.js_variant_change', function (ev) {
                var product_id = $('input.product_id');
                if (product_id.val()) {
                    gallery(product_id.val(), [200, 200], [400, 400], print_gallery);
                }
            });

            $(oe_website_sale).on('change', 'input.js_product_change', function (ev) {
                //console.debug("CHANGE GALLERY");
                var product_id = $(this).val();
                if (product_id) {
                    gallery(product_id, [200, 200], [400, 400], print_gallery);
                }
            });
        });


        // si hay variantes seleccionamos primero la imagen del template
        if ($('.js_product_change').length > 0) {
            var product_id = $('input.product_id').val();
            if (!product_id) {
                // seleccionamos un producto
                // if ($('input[name="product_id"]')) {
                //     var input = $('input[name="product_id"]').get(0);

                //     $(input).prop('checked', true);
                //     $(input).change();
                // }

                // seleccionar template
                var node = $('[data-oe-model="product.template"]');
                var tmpl_id = $(node).data("oe-id");
                if (tmpl_id) {
                    gallery_tmpl(tmpl_id, [200, 200], [400, 400], print_gallery);
                }
            }
        }
    });
})();
