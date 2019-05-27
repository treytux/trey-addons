odoo.define('website_sale_reset_styles.ribbon_wrappers', function (require) {
    'use strict'

    require('web.dom_ready');

    let $ribbon_wrappers = $('#products_grid .ribbon-wrapper')
    if($ribbon_wrappers.length) {
        $ribbon_wrappers.each(function(){
            $(this).appendTo($(this).closest('.oe_product'))
        })
    }
});
