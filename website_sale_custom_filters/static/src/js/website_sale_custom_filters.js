odoo.define('website_sale_custom_filters.website_sale', function (require) {
    'use strict';

    require('web.dom_ready');

    let $sorty_by = $('div.dropdown_sorty_by');
    let $ppg_by = $('div.dropdown_ppg_by');
    let $filter_bar = $('div.js_wscf_filter_bar');
    if($sorty_by.length && $filter_bar.length) {
        $sorty_by.appendTo($filter_bar)
    }
    if($ppg_by.length && $filter_bar.length) {
        $ppg_by.appendTo($filter_bar)
    }
});
