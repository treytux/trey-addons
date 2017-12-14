(function () {
    'use strict';

    openerp.website.ready().done(function() {
        $('.wishlist-item-add').each(function() {
            $(this).on('click', function(e) {
                e.preventDefault();
                openerp.jsonRpc('/shop/wishlist/add', 'call', {
                    'product_tmpl_id': $(this).attr('data-wl-product-id')
                }).then(function(result) {
                    if (result['error']) {
                        return;
                    } else {
                        $('[data-wl-product-id=' + result['product_tmpl_id'] + ']').find('i').removeClass('glyphicon-heart').addClass('glyphicon-ok');
                    }
                });
            });
        });
        $('.wishlist-add-items-to-cart').each(function() {
            $(this).on('click', function(e) {
                e.preventDefault();
                openerp.jsonRpc('/shop/wishlist/to_cart', 'call').then(function(result) {
                    if (result.empty) {
                        location.href = '/shop/cart';
                    } else {
                        _.each(result.lines_added, function(el){
                            $('[data-wl-line-id='+ result.lines_added[el] + ']').remove();
                        })
                        location.reload();
                    }
                });
            });
        });
        $('.wishlist-item-remove').each(function() {
            $(this).on('click', function(e) {
                e.preventDefault();
                openerp.jsonRpc('/shop/wishlist/remove', 'call', {
                    'line_id': $(this).attr('data-wl-item-id')
                }).then(function(result) {
                    if (result['error']) {
                        return;
                    }
                    else {
                        $('[data-wl-line-id='+ result.line_id + ']').remove();
                        if( result['empty'] ) {
                            location.reload();
                        }
                    }
                });
            });
        });
        $('.wishlist-empty').each(function() {
            $(this).on('click', function(e) {
                e.preventDefault();
                openerp.jsonRpc('/shop/wishlist/empty', 'call')
                    .then(function(result) {
                        if(result.response){
                            location.reload();
                        }
                    });
            });
        });
    });
})();
