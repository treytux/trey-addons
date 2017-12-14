(function() {
    'use strict';

    var _t = openerp._t;
    var website = openerp.website;

    website.website_sale_products_nav = {};

    website.website_sale_products_nav.NavSort = openerp.Widget.extend({
        init: function (parent) {
            var self = this;
            this._super(parent);
            var $sort = $('.js_wspn_sort_select');
            $sort.on('change', function(){
                var $ppg_selected = $('option:selected', this);
                document.location.href = $ppg_selected.data('link');
            });
        },
    });

    website.website_sale_products_nav.NavPPG = openerp.Widget.extend({
        init: function (parent) {
            var self = this;
            this._super(parent);
            var $ppg = $('.js_wspn_ppg_select');
            $ppg.on('change', function(){
                var $ppg_selected = $('option:selected', this);
                document.location.href = $ppg_selected.data('link');
            });
        },
    });

    website.ready().done(function() {
        website.if_dom_contains('.o_wspn_navbar', function ($el) {
            var nav_order = new website.website_sale_products_nav.NavSort();
            var nav_ppg = new website.website_sale_products_nav.NavPPG();
        });
    });
}());
