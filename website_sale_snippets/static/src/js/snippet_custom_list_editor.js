(function(){
    'use strict';
    var website = openerp.website;
    var session_editor = new openerp.Session();
    var _t = openerp._t;

    website.snippet.options.js_wss_custom_list = website.snippet.Option.extend({
        drop_and_build_snippet: function(){
            var self = this;
            if (!self.$target.data('snippet-view')) {
                this.$target.data('snippet-view', new website.snippet.animationRegistry.js_wss_custom_list(this.$target));
            }
        },
        clean_for_save:function(){
            this.$target.empty();
        }
    }),

    website.snippet.options.js_wss_custom_list_items = website.snippet.Option.extend({
        start:function(){
            var self = this;
            var default_items = 5;
            setTimeout(function(){
                var ul = self.$overlay.find('.snippet-option-js_wss_custom_list_items > ul');
                if (self.$target.attr('data-items')) {
                    var items = self.$target.attr('data-items');
                    ul.find('li[data-items="' + items + '"]').addClass('active');
                } else {
                    self.$target.attr('data-items', default_items);
                    ul.find('li[data-items="'+ default_items + '"]').addClass('active');
                }
            },100)
        },
        items:function(type, value, $li){
            var self = this;
            if(type != 'click'){ return }
            value = parseInt(value);
            this.$target.attr('data-items',value)
                .data('items',value)
                .data('snippet-view').redrow(true);
            setTimeout(function(){
                $li.parent().find('li').removeClass('active');
                $li.addClass('active');
            },100);
        }
    }),

    website.snippet.options.js_wss_custom_list_limit = website.snippet.Option.extend({
        start:function(){
            var self = this;
            var default_limit = 0;
            setTimeout(function(){
                var ul = self.$overlay.find('.snippet-option-js_wss_custom_list_limit > ul');
                if (self.$target.attr('data-limit')) {
                    var limit = self.$target.attr('data-limit');
                    ul.find('li[data-limit="' + limit + '"]').addClass('active');
                } else {
                    self.$target.attr('data-limit', default_limit);
                    ul.find('li[data-limit="'+ default_limit + '"]').addClass('active');
                }
            },100)
        },
        limit:function(type, value, $li){
            var self = this;
            if(type != 'click'){ return }
            value = parseInt(value);
            this.$target.attr('data-limit',value)
                .data('limit',value)
                .data('snippet-view').redrow(true);
            setTimeout(function(){
                $li.parent().find('li').removeClass('active');
                $li.addClass('active');
            },100);
        }
    }),

    website.snippet.options.js_wss_custom_list_image_size = website.snippet.Option.extend({
        start:function(){
            var self = this;
            var default_image_size = 'default';

            setTimeout(function(){
                var ul = self.$overlay.find('.snippet-option-js_wss_custom_list_image_size > ul');
                if (self.$target.attr('data-image_size')) {
                    var image_size = self.$target.attr('data-image_size');
                    ul.find('li[data-image_size="' + image_size + '"]').addClass('active');
                } else {
                    self.$target.attr('data-image_size', default_image_size);
                    ul.find('li[data-image_size="' + default_image_size + '"]').addClass('active');
                }
            },100)
        },
        image_size:function(type, value, $li){
            var self = this;

            if(type != 'click'){ return }
            this.$target.attr('data-image_size',value)
                .data('image_size',value)
                .data('snippet-view').redrow(true);
            setTimeout(function(){
                $li.parent().find('li').removeClass('active');
                $li.addClass('active');
            },100);
        }
    }),

    website.snippet.options.js_wss_custom_list_id = website.snippet.Option.extend({
        start: function() {
            this._super();
            var self        = this;
            var model       =  session_editor.model('custom.list');
            var custom_list = [];

            model.call('search_read', [
                [],
                ['name', 'id']
                ], {})
            .then(function(lists){
                self.createListSelector(lists)
            })
            .fail(function (e) {
                var title = _t('Oops, Huston we have a problem'),
                msg = $('<div contenteditable="false" class="message error text-center"><h3>'+ title +'</h3><code>'+ e.data.message + '</code></div>' );
                self.$target.append(msg)
                return;
            });
        },

        createListSelector: function(lists){
            var self = this;
            var ul = null;

            setTimeout(function(){
                if(lists.length > 0){
                    ul = self.$overlay.find('.snippet-option-js_wss_custom_list_id > ul');
                    $(lists).each(function(){
                        var list = $(this);
                        var li = $('<li data-list_id="' + list[0].id + '"><a>' + list[0].name + '</a></li>');
                        ul.append(li);
                    });
                    if (self.$target.attr('data-list_id')) {
                        var id = self.$target.attr('data-list_id');
                        var li = ul.find('li[data-list_id=' + id  + ']');
                    } else {
                        var li = ul.find('li[data-list_id]').first();
                        var id = li.attr('data-list_id');
                    }
                    self.list_id('click', id, li);
                }
            },100)
        },

        list_id:function(type, value, $li){
            var self = this;
            if(type == 'click'){
                $li.parent().find('li').removeClass('active');
                $li.addClass('active');
                value = parseInt(value);
                self.$target.attr('data-list_id',value)
                    .data('list_id',value)
                    .data('snippet-view').redrow(true);
            }
        }
    })
})();
