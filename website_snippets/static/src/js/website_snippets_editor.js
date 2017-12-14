'use strict';

(function () {
    var website = openerp.website;
    var qweb = openerp.qweb;
    var _t = openerp._t;

    website.add_template_file('/website_snippets/static/src/xml/website_snippets.xml');
    website.snippet.options.js_ws_snippet_toc_options = website.snippet.Option.extend({
        start:function(){
            var self = this;
            var $content = $('.oe_structure.oe_editable,#blog_content.oe_editable');
            var $tags = $content.find('h2,h3,h4,h5,h6');
            var $ul = self.$target.find('#o_wbt_collapse_toc ul');
            $ul.empty();
            $tags.each(function(index){
                var string = $(this).text();
                var id = self.slugify(string);
                var name = 'o_wbt_toc_' + $(this).prop('tagName').toLowerCase();
                var $toc_item = $(qweb.render('toc_item',{'id': id, 'name': name, 'string': string}));
                $ul.append($toc_item);
                $(this).attr('id', id);
            });
        },
        slugify:function(str){
            var from = "ãàáäâẽèéëêìíïîõòóöôùúüûñç·/_,:;";
            var to   = "aaaaaeeeeeiiiiooooouuuunc------";
            str = str.replace(/^\s+|\s+$/g, '');
            str = str.toLowerCase();
            for (var i=0, l=from.length ; i<l ; i++) {
                str = str.replace(new RegExp(from.charAt(i), 'g'), to.charAt(i));
            }
            return str.replace(/[^a-z0-9 -]/g, '').replace(/\s+/g, '-').replace(/-+/g, '-');
        }
    });
})();
