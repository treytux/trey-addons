(function () {
    'use strict';
    var website = openerp.website;

    website.ready().done(function () {
        let $products_grid_before = $('#products_grid_before')
        let $js_wscf_filters_panel_body = $('.js_wscf_filters_panel_body')
        if($products_grid_before.length && $js_wscf_filters_panel_body.length) {
            $products_grid_before.clone().appendTo($js_wscf_filters_panel_body)
        }
    });
}());
