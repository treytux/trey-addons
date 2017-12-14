(function() {
    'use strict';
    var website = openerp.website;
    var _t = openerp._t;

    website.snippet.options.js_wfp_fb_comments_options = website.snippet.Option.extend({
        start:function(){
            var self = this;
            var default_numposts = '5';
            var default_width = '100%';

            setTimeout(function(){
                var ul = self.$overlay.find('.snippet-option-js_wfp_fb_comments_options > ul');
                // option: numposts
                if (self.$target.attr('data-numposts')) {
                    var numposts = self.$target.attr('data-numposts');
                    ul.find('li[data-numposts="' + numposts + '"]').addClass('active');
                } else {
                    self.$target.attr('data-numposts', default_numposts);
                    ul.find('li[data-numposts="' + default_numposts + '"]').addClass('active');
                }
                // option: width
                if (self.$target.attr('data-width')) {
                    var width = self.$target.attr('data-width');
                    ul.find('li[data-width="' + width + '"]').addClass('active');
                } else {
                    self.$target.attr('data-width', default_width);
                    ul.find('li[data-width="' + default_width + '"]').addClass('active');
                }
            },100)
        },
        numposts:function(type, value, $li){
            var self = this;

            if(type != 'click'){ return }
            this.$target.attr('data-numposts', value);
            setTimeout(function(){
                $li.parent().find('li').removeClass('active');
                $li.addClass('active');
            },100);
        },
        width:function(type, value, $li){
            var self = this;

            if(type != 'click'){ return }
            this.$target.attr('data-width', value);
            setTimeout(function(){
                $li.parent().find('li').removeClass('active');
                $li.addClass('active');
            },100);
        },
        // on_focus:function(){ console.log('on_focus'); },
        // on_blur:function(){ console.log('on_blur'); },
        // on_clone:function(){ console.log('on_clone'); },
        // on_focus:function(){ console.log('on_focus'); },
        // on_remove:function(){ console.log('on_remove'); },
        // drop_and_build_snippet:function(){ console.log('drop_and_build_snippet'); },
        // clean_for_save:function(){ console.log('clean_for_save'); },
    });

    website.snippet.options.js_wfp_fb_page_options = website.snippet.Option.extend({
        start:function(){
            var self = this;
            var default_tabs = '';
            var default_hide_cover = 'false';

            setTimeout(function(){
                var ul = self.$overlay.find('.snippet-option-js_wfp_fb_page_options > ul');
                // option: tabs
                if (self.$target.attr('data-tabs')) {
                    var tabs = self.$target.attr('data-tabs');
                    ul.find('li[data-tabs="' + tabs + '"]').addClass('active');
                } else {
                    self.$target.attr('data-tabs', default_tabs);
                    ul.find('li[data-tabs="' + default_tabs + '"]').addClass('active');
                }
                // option: hide_cover
                if (self.$target.attr('data-hide_cover')) {
                    var hide_cover = self.$target.attr('data-hide_cover');
                    ul.find('li[data-hide_cover="' + hide_cover + '"]').addClass('active');
                } else {
                    self.$target.attr('data-hide_cover', default_hide_cover);
                    ul.find('li[data-hide_cover="' + default_hide_cover + '"]').addClass('active');
                }
            },100)
        },
        tabs:function(type, value, $li){
            var self = this;

            if(type != 'click'){ return }
            this.$target.attr('data-tabs',value);
            setTimeout(function(){
                $li.parent().find('li').removeClass('active');
                $li.addClass('active');
            },100);
        },
        hide_cover:function(type, value, $li){
            var self = this;

            if(type != 'click'){ return }
            this.$target.attr('data-hide_cover',value);
            setTimeout(function(){
                $li.parent().find('li').removeClass('active');
                $li.addClass('active');
            },100);
        },
    });
})();
