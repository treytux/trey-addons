(function () {
    'use strict';
    var website = openerp.website,
    ajax = openerp;
    website.add_template_file('/website_sale_products_pricelist/static/src/xml/pricelist_table.xml');
    website.website_sale_products_pricelist = {};
    website.website_sale_products_pricelist.GridRow = openerp.Widget.extend({
        template: 'website.wspp_table_row',

        init: function (parent, options) {
            this.qty = options.qty;
            this.product_id = options.product_id;
            this.unit_price = options.unit_price;
            this._super(parent);
        },
    });

    // website.website_sale_products_pricelist.Grid = openerp.Widget.extend({
    //     dom_ready: $.Deferred(),
    //     ready: function(){
    //         return this.dom_ready.then(function() {}).promise();
    //     },
    //     init: function (parent, options) {
    //         var self = this;
    //         this._super(parent);
    //         var $promos = $('.wsp_pricelist');
    //         if ($promos != {}){
    //             $promos.each(function() {
    //                 $(this).on('click', function(e) {
    //                     e.preventDefault();
    //                     var promo = $(this).data('promo'),
    //                         product_id = $(this).data('product_id');
    //                     self.insert_rows(product_id, promo[product_id]);
    //                 });
    //             });
    //         }
    //     },
    //     insert_rows: function(product_id, promo){
    //         var $table = $('.js_wsp_pricelist_table')
    //         , $modalBody = $('.modal-tbody');
    //         if (promo){
    //             $table.removeClass('hidden');
    //             $modalBody.empty();
    //             return ajax.jsonRpc("/shop/product_prices", 'call', {
    //                 'product_id': product_id,
    //                 'qtys': promo}
    //             ).then(function (data) {
    //                 $(data).each(function(){
    //                     var line = this.split("-"),
    //                         qty = line[0],
    //                         unit_price = line[1];
    //                     new website.website_sale_products_pricelist.GridRow(
    //                         this,
    //                         {   qty: qty,
    //                             product_id: product_id,
    //                             unit_price: unit_price,
    //                         }
    //                     ).appendTo($modalBody);
    //                 });
    //                 var buttons_add = $(".btn-qyt-pricelist-cart-modal");
    //                 buttons_add.each(function(){
    //                     $(this).on("click", function(ev) {
    //                         ev.preventDefault();
    //                         var $link = $(ev.currentTarget),
    //                             quantity = parseInt($link.data('qty'));
    //                         openerp.jsonRpc("/shop/cart/update_json", 'call', {
    //                             'line_id': null,
    //                             'product_id': parseInt($link.data('product_id'), 10),
    //                             'add_qty': parseInt($link.data('qty'))
    //                         }).then(function (data) {
    //                             if (!data.quantity) {
    //                                 location.reload();
    //                                 return;
    //                             }
    //                             $('#promoModal').modal('hide');
    //                             var $q = $(".my_cart_quantity");
    //                             $q.parent().parent().removeClass("hidden", !data.quantity);
    //                             $q.html(data.cart_quantity).hide().fadeIn(600, function(){
    //                                 alert('El producto se ha añadido al carrito.');
    //                             });
    //                             $("#cart_total").replaceWith(data['website_sale.total']);
    //                         });
    //                         return false;
    //                     });
    //                 });
    //                 return false
    //             });
    //         }
    //     },
    // });

    website.website_sale_products_pricelist.Product_grid = openerp.Widget.extend({
        ready: function(){
            return this.dom_ready.then(function() {}).promise();
        },

        init: function (parent, options) {
            var self = this;
            this._super(parent);
            if ($('input.js_wsp_pricelist').data('promo') != null){

                self.insert_rows();
                $('.oe_website_sale').each(function () {
                    var oe_website_sale = this;
                    $(oe_website_sale).on('change','input.js_variant_change, select.js_variant_change', function (ev) {
                        $('.modal-tbody').empty();
                        $('.js_wsp_pricelist_table').addClass('hidden');
                        self.insert_rows();
                    });
                });
            }
        },

        insert_rows: function(){
            var product_id = parseInt($('input.product_id').val())
            , promo = $('input.js_wsp_pricelist').data('promo')
            , $table = $('.js_wsp_pricelist_table')
            , $modalBody = $('.modal-tbody')
            , promo_prod = promo[parseInt(Object.keys(promo))]
            , array_product = promo_prod[product_id];

            if (array_product){
                $table.removeClass('hidden');
                $(Object.keys(array_product)).each(function(){
                    var line = array_product[this].split("-"),
                    qty = line[0],
                    unit_price = line[1];

                    new website.website_sale_products_pricelist.GridRow(
                        this,
                        {   qty: qty,
                            product_id: product_id,
                            unit_price: unit_price,
                        }).appendTo($modalBody);
                });
                $(".btn-qyt-pricelist-cart-modal").on("click", function(ev) {
                    ev.preventDefault();
                    var $link = $(ev.currentTarget)
                    , quantity = parseInt($link.data('qty'));

                    openerp.jsonRpc("/shop/cart/update_json", 'call', {
                        'line_id': null,
                        'product_id': parseInt($link.data('product_id'), 10),
                        'add_qty': quantity})
                        .then(function (data) {
                            if (!data.quantity) {
                                location.reload();
                                return;
                            }
                            var $q = $(".my_cart_quantity");
                            $q.parent().parent().removeClass("hidden", !data.quantity);
                            $q.html(data.cart_quantity).hide().fadeIn(600, function(){
                                alert('El producto se ha añadido al carrito.');
                            });
                            $("#cart_total").replaceWith(data['website_sale.total']);
                        });
                    return false;
                });

            }else{
                $table.addClass('hidden');
                $modalBody.empty();
            }
        },

    });

    website.ready().done(function () {
        // website.if_dom_contains('.wsp_pricelist', function ($el) {
        //     new website.website_sale_products_pricelist.Grid();
        // });
        website.if_dom_contains('.js_wsp_pricelist_table', function ($el) {
            new website.website_sale_products_pricelist.Product_grid();
        });
    });
}());
