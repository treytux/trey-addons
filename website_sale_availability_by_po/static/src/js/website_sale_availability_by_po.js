odoo.define('website_sale_availability_by_po.product_availability', function (require) {
    "use strict";

    require('web.dom_ready');
    let ajax = require('web.ajax');

    function apply_availability(data, index, obj){
        let stock = data[index];
        if (stock.stock_state == 'coming_soon' && !stock.date_planned) {
            stock.stock_state = 'coming_soon_without_date_planned'
        }
        for (let property in stock) {
            if (stock.hasOwnProperty(property)) {
                obj.find('.o_wsabpo_available_msg.o_wsabpo_' + stock.stock_state).attr(property, stock[property])
            }
        }
        obj.find('.o_wsabpo_available_msg').fadeOut('fast');
        obj.find('.o_wsabpo_available_msg').removeClass('o_wsabpo_has_extra_msg');
        obj.find('.o_wsabpo_extra_msg').remove();
        obj.find('.o_wsabpo_available_msg.o_wsabpo_' + stock.stock_state).fadeIn('fast');
        if(stock.stock_state == 'coming_soon'){
            obj.find('.o_wsabpo_available_msg.o_wsabpo_coming_soon .o_wsabpo_planned_for').text(stock.date_planned);
        }
        if(stock.hasOwnProperty('extra_msg')){
            obj.find('.o_wsabpo_available_msg.o_wsabpo_' + stock.stock_state).addClass('o_wsabpo_has_extra_msg')
            obj.find('.o_wsabpo_available_msg.o_wsabpo_' + stock.stock_state + ' .label span').after(' <span class="o_wsabpo_extra_msg">' + stock.extra_msg + '</span>');
        }
    }

    let $detail_products = $('#product_details input[name="product_id"]');
    if($detail_products.length) {
        let product_ids = $detail_products.map(function(){return Number($(this).attr('value'));}).get()
        ajax.jsonRpc('/shop/product_availability', 'call', {
            'product_ids': product_ids
        }).then(function (data) {
            $detail_products.each(function(){
                apply_availability(data, $(this).attr('value'), $(this).closest('#product_details'))
            })
        });
    }

    let $list_products = $('#products_grid input[name="product_id"]');
    if($list_products.length) {
        let product_ids = $list_products.map(function(){return Number($(this).attr('value'));}).get()
        ajax.jsonRpc('/shop/product_availability', 'call', {
            'product_ids': product_ids
        }).then(function (data) {
            $list_products.each(function(){
                apply_availability(data, $(this).attr('value'), $(this).closest('form'))
            })
        });
    }
});
