// License, author and contributors information in:
// __openerp__.py file at the root folder of this module.
(function () {
    "use strict";
    var website = openerp.website;
    website.add_template_file(
        '/website_seo_url/static/src/xml/website_seo.xml');

    website.seo.HtmlPage = website.seo.HtmlPage.extend({
        changeUrl: function (url) {
            this.url_slug = url;
        },
        url: function() {
            return document.location.protocol + '//' +
                   document.location.host + (
                    this.url_slug ?
                    '/' + this.url_slug :
                    document.location.pathname);
        },
    });

    website.seo.Configurator.include({
        init: function(parent, options) {
            var self = this;

            self._super(parent, options);
            self.events['keyup input[data-slug]'] = 'slugChanged';
        },
        loadMetaData: function () {
            return $.when(this._super(), this.loadSlug());
        },
        loadSlug: function() {
            var self = this;
            self.slug_widget = null;

            var params = [
                $('html').data('slug-path'), website.get_context()];
            var model = website.session.model('website_seo_url.slug');
            model.call('load_slug', params).then(function (slug) {
                self.$el.find('.js_seo_url_loading').addClass('hide');
                self.slug_widget = new website.seo.Slugs(
                    self, slug);
                self.slug_widget.appendTo(
                    self.$el.find('.js_seo_url_section'));
            });
        },
        saveMetaData: function (data) {
            var self = this;
            var def = $.Deferred();

            return self._super(data).then(function(){
                self.saveSlug().then(function(data){
                    self.onSaveSlug(data);
                });
            });
        },
        saveSlug: function () {
            var self = this;
            var obj = self.getMainObject();
            var def = $.Deferred();
            var path = $('html').data('slug-path');
            var old_slug = document.location.pathname;
            var new_slug = this.$el.find('input[data-slug]').val();

            if (old_slug === '/' + new_slug) {
                return def;
            }

            return website.session.model('website_seo_url.slug').call(
                'save_slug',
                [new_slug, path, obj.model, obj.id, website.get_context()]
            );
        },
        onSaveSlug: function (data) {
            var self = this;
            if(data && 'redirect' in data) {
                document.location = data.redirect + document.location.search;
            }
        },
        slugChanged: function () {
            var self = this;

            setTimeout(function () {
                var url = self.$(
                    'input[data-slug]').val();
                self.htmlPage.changeUrl(url);
                self.renderPreview();
            }, 0);
        },
    });

    website.seo.Slugs = openerp.Widget.extend({
        template: 'website_seo_url.slug_form',
        events: {
            'closed.bs.alert': 'destroy',
        },
        init: function(parent, slug) {
            var self = this;

            self.parent = parent;
            self.protocol = document.location.protocol;
            self.host = document.location.host;
            self.slug = slug;
            self._super();
        },
    });
})();
