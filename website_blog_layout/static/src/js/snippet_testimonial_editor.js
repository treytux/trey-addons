(function() {
    'use strict';
    var website = openerp.website;
    var _t = openerp._t;

    website.snippet.options.snippet_testimonial_size = website.snippet.Option.extend({
        start:function(){
            var self = this;
            var default_image_size = 'default';

            setTimeout(function(){
                var ul = self.$overlay.find('.snippet-option-snippet_testimonial_size > ul');
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
                .data('image_size',value);
            setTimeout(function(){
                $li.parent().find('li').removeClass('active');
                $li.addClass('active');
            },100);
        }
    }),

    website.snippet.options.snippet_testimonial_options = website.snippet.Option.extend({
        start:function(){
            alert("On start!");
        },
        on_focus: function() {
            alert("On focus!");
        }
        // drop_and_build_snippet: function(){
        //     var self = this;
        //     if (!self.$target.data('snippet-view')) {
        //         this.$target.data('snippet-view', new website.snippet.animationRegistry.snippet_testimonial_options(this.$target));
        //     }
        // },
        // clean_for_save:function(){
        //     this.$target.empty();
        // }
        // METHODS
        // start   Fires when the publisher selects the snippet for the first time in an editing session or when the snippet is drag-dropped into the page
        // on_focus    Fires each time the snippet is selected by the user or when the snippet is drag-dropped into the page.
        // on_blur This event occurs when a snippet loses focus.
        // on_clone    Fires just after a snippet is duplicated. A new js variable is created ($clone) containing the cloned element.
        // on_remove   It occurs just before that the snippet is removed.
        // drop_and_build_snippet  Fires just after that the snippet is drag and dropped into a drop zone. When this event is triggered, the content is already inserted in the page.
        // clean_for_save  It trigger before the publisher save the page.
    });
})();

// (function() {
//     'use strict';
//     var website = openerp.website;
//     website.openerp_website = {};

//     website.snippet.options.snippet_testimonial_options = website.snippet.Option.extend({
//         on_focus: function() {
//             alert("On focus!");
//         }
//     })
// })();
// (function() {
//     'use strict';

//     var _t = openerp._t;
//     var website = openerp.website;

//     website.openerp_website = {};

//     website.snippet.options.snippet_testimonial_options = website.snippet.Option.extend({
//         on_focus: function() {
//             alert("On focus!");
//         }
//     })

//     website.ready().done(function() {
//         console.log('Blog layout!');
//         // openerp.website.if_dom_contains('body[data-view-xmlid="website_sale.product"]', function() {
//         //     if($('.wspis_in_stock_msg').length == 1 && $('input[name="js_naparbier_sale_delay"]').length == 1){
//         //         $('.wspis_in_stock_msg').text($('.wspis_in_stock_msg').text() + '. ' + _t('Get it in ') + ' ' + $('input[name="js_naparbier_sale_delay"]').val() + ' ' + _t('days!'));
//         //     }
//         // });
//     });
// })();
