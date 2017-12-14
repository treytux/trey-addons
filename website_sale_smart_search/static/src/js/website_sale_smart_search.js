(function() {
    'use strict';

    var instance = openerp;
    var website = openerp.website;

    website.add_template_file('/website_sale_smart_search/static/src/xml/website_sale_smart_search.xml');
    website.smart_search = {};

    website.smart_search.SmartSearch = openerp.Widget.extend({
        dom_ready: $.Deferred(),
        ready: function(){
                return this.dom_ready.then(function() {}).promise();
            },
        init: function (parent, options) {
            this.dom_ready.resolve();
            var timeout = null;
            var last_value = '';
            var value = '';
            var query_length = parseInt($('.js_wsss_results').data('query_length'));
            $('input[name=search]').on('keyup', (function (e){
                var self = this;
                if (timeout !== null){
                    clearTimeout(timeout);
                }
                timeout = setTimeout(function(){
                    if (self.value.length < query_length){
                        $('.js_wsss_results').addClass('hidden');
                        return;
                    }
                    if($('.js_wsss_results').hasClass('hidden')) {
                        self.last_value = '';
                    }
                    if (self.value == self.last_value){
                        return;
                    } else {
                        self.last_value = self.value;
                        $('.js_wsss_banner').empty();
                        $('ul.js_wsss_category_items').empty();
                        $('ul.js_wsss_items').empty();
                        $('.js_wsss_results').removeClass('hidden');
                    }
                    openerp.jsonRpc('/smart-search/search', 'call', {
                        'search': self.value
                    }).then(function(data){
                        // TODO: Resaltar las palabras de búsqueda en los resultados class="o_wsss_match"
                        var i;
                        if (data['banner'] != null){
                            new website.smart_search.SmartSearchItemBanner(self, {
                                data: data['banner']}).appendTo($('.js_wsss_banner'));
                        }
                        if (data['categories'].length > 0){
                            for (i = 0; i < data['categories'].length; i++){
                                new website.smart_search.SmartSearchItemCategory(self, {
                                    data: data['categories'][i]}).appendTo($('ul.js_wsss_category_items'));
                            }
                        }
                        $('.js_wsss_searches_qty').text(data['products'].length);
                        if (data['products'].length > 0){
                            for (i = 0; i < data['products'].length; i++){
                                var item = new website.smart_search.SmartSearchItem(self, {
                                    data: data['products'][i]});
                                item.appendTo($('ul.js_wsss_items'));
                            }
                            $('.o_wsss_item a').each(function() {
                                $(this).on('click', (function(e) {
                                    e.preventDefault();
                                    var href = $(this).attr('href');
                                    openerp.jsonRpc('/smart-search/hit', 'call', {
                                        'search': self.value,
                                        'url': href
                                    });
                                    document.location = href;
                                }));
                            });
                        }
                    });
                }, 500);
            }));
            this._super(parent);
        },
    });

    website.smart_search.SmartSearchItem = openerp.Widget.extend({
        template: 'website.search_results_item',
        init: function (parent, options) {
            this.id = options.data.id;
            this.name = options.data.name;
            this.description = options.data.description;
            this.price = options.data.price;
            this.lst_price = options.data.lst_price;
            this.formatted_price = this.format_value(options.data.price);
            this.formatted_lst_price = this.format_value(options.data.lst_price);
            this.currency = options.data.currency;
            this.publish = options.data.publish;
            this._super(parent);
        },
        format_value: function (value) {
            // TODO: Use format_value in web/static/src/js/formats.js instead
            // of this function
            var digits = [69,2];
            var precision = digits[1];
            var formatted = _.str.sprintf('%.' + precision + 'f', value).split('.');

            return formatted.join(',');
        }
    });

    website.smart_search.SmartSearchItemBanner = openerp.Widget.extend({
        template: 'website.search_results_item_banner',
        init: function (parent, options) {
            this.id = options.data.id;
            this.href = options.data.href;
            this._super(parent);
        },
    });

    website.smart_search.SmartSearchItemCategory = openerp.Widget.extend({
        template: 'website.search_results_item_category',
        init: function (parent, options) {
            this.id = options.data.id;
            this.name = options.data.name;
            this.products = options.data.products;
            this._super(parent);
        },
    });

    website.ready().done(function() {
        openerp.website.if_dom_contains('input[name="search"]', function() {
            new website.smart_search.SmartSearch();
            $('.js_wsss_close_btn').on('click', (function(e) {
                $('.js_wsss_results').addClass('hidden');
            }));
            $('.js_wsss_list_btn').on('click', (function(e) {
                $('.js_wsss_items').removeClass('o_wsss_items_grid');
            }));
            $('.js_wsss_grid_btn').on('click', (function(e) {
                $('.js_wsss_items').addClass('o_wsss_items_grid');
            }));
        });
    });
}());
