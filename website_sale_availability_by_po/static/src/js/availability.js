odoo.define('website_sale_availability_by_po.product_availability', function (require) {
    "use strict";

    require('web.dom_ready');
    let ajax = require('web.ajax');
    let lastPid = null;

    function apply_availability(data, index, obj){
        let stock = data[index];
        if (!stock) { return; }
        if (stock.stock_state == 'coming_soon' && !stock.date_planned) {
            stock.stock_state = 'coming_soon_without_date_planned';
        }
        for (let property in stock) {
            if (stock.hasOwnProperty(property)) {
                obj.find('.o_wsabpo_available_msg.o_wsabpo_' + stock.stock_state).attr(property, stock[property]);
            }
        }
        obj.find('.o_wsabpo_available_msg').fadeOut('fast');
        obj.find('.o_wsabpo_available_msg').removeClass('o_wsabpo_has_extra_msg');
        obj.find('.o_wsabpo_extra_msg').remove();
        obj.find('.o_wsabpo_available_msg.o_wsabpo_' + stock.stock_state).hide().fadeIn('fast');
        if (stock.stock_state == 'coming_soon') {
            obj.find('.o_wsabpo_available_msg.o_wsabpo_coming_soon .o_wsabpo_planned_for').text(stock.date_planned || '');
        }
        if (stock.hasOwnProperty('extra_msg')){
            obj.find('.o_wsabpo_available_msg.o_wsabpo_' + stock.stock_state).addClass('o_wsabpo_has_extra_msg');
            obj.find('.o_wsabpo_available_msg.o_wsabpo_' + stock.stock_state + ' .label span').after(' <span class="o_wsabpo_extra_msg">' + stock.extra_msg + '</span>');
        }
    }
    let $detail_products = $('#product_details input[name="product_id"]');
    if ($detail_products.length) {
        let product_ids = $detail_products.map(function(){ return Number($(this).val()); }).get();
        ajax.jsonRpc('/shop/product_availability', 'call', {
            'product_ids': product_ids
        }).then(function (data) {
            $detail_products.each(function(){
                apply_availability(data, $(this).val(), $(this).closest('#product_details'));
            });
        });
        $(document)
          .off('change.wsabpo', '#product_details input[name="product_id"]')
          .on('change.wsabpo', '#product_details input[name="product_id"]', function () {
            const pid = Number($(this).val());
            if (!pid || pid === lastPid) { return; }
            ajax.jsonRpc('/shop/product_availability', 'call', {
                'product_ids': [pid]
            }).then(function (data) {
                apply_availability(data, pid, $('#product_details'));
                lastPid = pid;
            });
        });
    }
});
