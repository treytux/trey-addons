odoo.define('website_sale_collapse_filters.filters', function (require) {
    'use strict';
    require('web.dom_ready')
    let $products_grid_before = $('#products_grid_before')
    let $js_wscf_filters_panel_body = $('.js_wscf_filters_panel_body')
    if($products_grid_before.length && $js_wscf_filters_panel_body.length) {
        $products_grid_before.clone().appendTo($js_wscf_filters_panel_body)
    }
})
