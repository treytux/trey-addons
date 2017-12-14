(function(){
    'use strict';
    var website = openerp.website;
    var _t = openerp._t;

    website.snippet.animationRegistry.js_wss_custom_list = website.snippet.Animation.extend({
        selector : '.js_wss_custom_list',

        start: function(){
            this.redrow();
        },
        stop: function(){
            this.clean();
        },

        redrow: function(debug){
            this.clean(debug);
            this.build(debug);
        },

        clean:function(debug){
            this.$target.empty();
        },

        build: function(debug){
            var self       = this;
            var items      = self.$target.data('items');
            var limit      = self.$target.data('limit');
            var image_size = self.$target.data('image_size');
            var list_id    = self.$target.data('list_id');

            self.$target.attr('contenteditable','False');

            if(!limit) limit = 0;
            if(!image_size) image_size = 'default';

            var domain = [['custom_list_id', '=', parseInt(list_id)]]
            $.get('/website_sale_snippets/custom_list/render', {
                'limit': limit,
                'list_id': list_id,
                'image_size': image_size
            }).done(function(products) {
                $(products).appendTo(self.$target);
                var owl_options = {
                    items: items,
                    navigationText: [_t('prev'), _t('next')],
                    lazyLoad: true,
                    navigation: true
                };
                self.$target.find('.owl-carousel').owlCarousel(owl_options);
            }).fail(function(e) {
                return;
            });
        }
    })
})();
