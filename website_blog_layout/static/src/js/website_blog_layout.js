(function() {
    'use strict';

    var _t = openerp._t;
    var website = openerp.website;

    website.ready().done(function() {
        console.log('Blog layout!');
        // openerp.website.if_dom_contains('body[data-view-xmlid="website_sale.product"]', function() {
        //     if($('.wspis_in_stock_msg').length == 1 && $('input[name="js_naparbier_sale_delay"]').length == 1){
        //         $('.wspis_in_stock_msg').text($('.wspis_in_stock_msg').text() + '. ' + _t('Get it in ') + ' ' + $('input[name="js_naparbier_sale_delay"]').val() + ' ' + _t('days!'));
        //     }
        // });
    });
})();
