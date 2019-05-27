odoo.define('website_sale_collapse_filters.collapse_filters', function (require) {
    'use strict'
    require('website_sale.website_sale')

    let $products_grid_before = $('#products_grid_before')
    let $js_wscf_filters_panel_body = $('.js_wscf_filters_panel_body')
    if($products_grid_before.length && $js_wscf_filters_panel_body.length) {
        $products_grid_before.clone().appendTo($js_wscf_filters_panel_body)
    }
});
