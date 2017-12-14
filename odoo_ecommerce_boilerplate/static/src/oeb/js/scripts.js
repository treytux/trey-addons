document.addEventListener('DOMContentLoaded', function(){
    jQuery(document).ready(function($){

        // // COMPORTAMIENTO MENÚ PRINCIPAL

        // $('#top_menu').before('<ul class="nav navbar-nav navbar-right navbar-widgets"><li class="widget-user"></li><li class="widget-cart"></li></ul>');
        // $('#top_menu').after('<ul class="nav navbar-nav navbar-right"><li class="widget-search"></li></ul>');
        // $('#top_menu').removeClass('navbar-right');
        // $('#top_menu').addClass('navbar-left');
        // $('#top_menu a[href="/shop/cart"]').prependTo('.widget-cart');
        // $('#top_menu .js_usermenu').closest('.dropdown').prependTo('.widget-user');
        // $('.products_pager form.pagination').prependTo('.widget-search').removeClass('col-md-3');

        // // COMPORTAMIENTO MENÚ LATERAL CATEGORÍAS

        // // Desplegamos los submenús hasta la categoría activa
        // $('.nav.categories').each(function(e){
        //     var activeElements = $(this).find('.active');
        //     if( activeElements.length > 0 ) {
        //         activeElements.each(function(){
        //             activeElements.find('a').first().addClass('opened');
        //             $(this).parents('.nav-hierarchy').show();
        //             $(this).parents('.nav-hierarchy').prev().addClass('opened');
        //             $(this).find('.nav-hierarchy').first().show();
        //         });
        //     }
        // });

        // // Aplicamos el comportamiento para los enlaces
        // var categoriesNavigation = $('.nav.categories');
        // categoriesNavigation.find('.active a').each(function(e){
        //     if( $(this).attr('href') == window.location.pathname ) {
        //         $(this).addClass('active-item');
        //     }
        // });
        // categoriesNavigation.find('.nav-hierarchy').each(function(e){
        //     $(this).prev().addClass('has-childs');
        // });
        // categoriesNavigation.find('a').each(function(e){
        //     childs = $(this).parent().find('.nav-hierarchy').first();
        //     if( childs.length > 0 ) {
        //         // Si tiene hijos desplegamos el submenú
        //         $(this).parent().find('.nav-hierarchy').first().prepend('<li>');
        //         $(this).clone().appendTo( $(this).parent().find('.nav-hierarchy').first().find('li').first() );
        //         $(this).parent().find('.nav-hierarchy').first().find('li').first().find('a').html('Ver todo');
        //         $(this).parent().find('.nav-hierarchy').first().find('li').first().find('a').removeClass('has-childs');
        //     }
        // });
        // categoriesNavigation.find('a').on('click', function(e){
        //     e.preventDefault();
        //     if( $(this).hasClass('opened') ) {
        //         $(this).removeClass('opened');
        //     } else {
        //         $(this).addClass('opened');
        //     }
        //     childs = $(this).parent().find('.nav-hierarchy').first();
        //     if( childs.length > 0 ) {
        //         // Si tiene hijos desplegamos el submenú
        //         $(this).parent().find('.nav-hierarchy').first().toggle();
        //     } else {
        //         // Si no tiene hijos vamos al listado de productos de la categoría
        //         window.location.href = $(this).attr('href');
        //     }
        // });

        // $("input.js_quantity_list").on("change", function(ev) {
        //     ev.preventDefault();
        //     var $input = $(this);
        //     var quantity = $input.val();

        //     if (isNaN(quantity))
        //         quantity = 1;

        //     if (quantity < 1)
        //         quantity = 1;

        //     $input.val(quantity);
        // });

        // $(".fa-shopping-cart-ajax-btn").on("click", function(ev) {
        //     ev.preventDefault();
        //     var $link = $(ev.currentTarget);
        //     var $input = $link.parent().find(".js_quantity_list");
        //     var quantity = parseFloat($input.val(), 10);

        //     openerp.jsonRpc("/shop/cart/update_json", 'call', {
        //         'line_id': null,
        //         'product_id': parseInt($input.data('product-id'), 10),
        //         'add_qty': quantity})
        //         .then(function (data) {
        //             if (!data.quantity) {
        //                 location.reload();
        //                 return;
        //             }
        //             var $q = $(".my_cart_quantity");
        //             $q.parent().parent().removeClass("hidden", !data.quantity);
        //             $q.html(data.cart_quantity).hide().fadeIn(600, function(){
        //                 alert('El producto se ha añadido al carrito.');
        //             });

        //             $input.val(1);
        //             $("#cart_total").replaceWith(data['website_sale.total']);
        //         });

        //     return false;
        // });

        // if ($('#payment_direct_order_form')) {
        //     $('button', $('#payment_direct_order_form')).click();
        // }

    });
});
