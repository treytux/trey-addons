(function () {
    'use strict';

    var website = openerp.website;
    website.add_template_file(
        '/website_url_friendly/static/src/xml/website.seo.xml');

    website.seo.HtmlPage = website.seo.HtmlPage.extend({
        changeUrl: function (url) {
            this.url_slug = url;
        },
        url: function() {
            var url = window.location.href;
            var hashIndex = url.indexOf('#');

            if (this.url_slug) {
                var urlslug = window.location.protocol + '//' +
                    window.location.host + '/' + this.url_slug;
                return urlslug
            } else {
                return hashIndex >= 0 ? url.substring(0, hashIndex) : url;
            }
        },
    });

    website.seo.Configurator = website.seo.Configurator.extend({
        init: function(parent, options) {
            var self = this;

            self._super(parent, options);
            self.slug_widget = null;
            self.events['keyup input[name=slug]'] = 'slugChanged';
        },
        loadSlug: function() {
            var self = this,
                obj = this.getMainObject(),
                $input = self.$('input[name=slug]'),
                def = $.Deferred(),
                path = $('html').data('slug-path');

            if (path == '/' || path == '/page/homepage') {
                self.$el.find('.js_seo_url_section').addClass('hide');
                def.reject();
                return def;
            }

            if (!obj) {
                self.$el.find('.js_seo_url_section').addClass('hide');
                def.reject();
                return def;
            }
            var params = {
                'path': path, 'model': obj.model, 'model_id': obj.id};

            $.getJSON("/website_url_friendly/load", params, function(slug) {
                if(!slug){
                    self.$el.find('.js_seo_url_section').addClass('hide');
                    def.reject();
                } else {
                    self.$el.find('.js_seo_url_loading').addClass('hide');
                    self.slug_widget = new website.seo.Slugs(
                        self, slug);
                    self.slug_widget.appendTo(
                        self.$el.find('.js_seo_url_section'));
                }
                // if (resp['empty']) {
                //     self.$el.find('.js_seo_url_section').addClass('hide');
                //     def.reject();
                // } else {
                //     self.$el.find('.js_seo_url_loading').html('');
                //     self.slug_widget = new website.seo.Slugs(
                //         self, resp['slugs']);
                //     self.slug_widget.appendTo(self.$el.find('.js_seo_url_loading'));
                // }
            });

            return def;
        },
        saveSlug: function() {
            var self = this;
            var obj = self.getMainObject();
            var def = $.Deferred();
            var path = $('html').data('slug-path');
            var $input = self.$('input[data-slug]');

            if($input.data('slug') != $input.val()){
                var new_slug = {
                    'name': $input.data('slug'),
                    'new_name': $input.val(),
                    'lang_code': $input.data('lang_code')};
                $.getJSON('/website_url_friendly/save_slugs', {
                    'new_slug': JSON.stringify(new_slug),
                    'path': path,
                    'model': obj.model,
                    'model_id': obj.id
                }, function(data) {
                    if('errors' in data){
                        // TODO: Show errors before slug input
                        console.log(data.errors);
                    } else if('slug' in data){
                        $input.attr('data-slug', data.slug.name);
                    }
                    if('redirect' in data){
                        window.location = data.redirect;
                    }
                    // if (resp['action'] == 'none')
                    //     return def.resolve(true);
                    // else if (resp['action'] == 'home')
                    //     return window.location = '/';
                    // else if (resp['action'] == 'error')
                    //     return alert("ERROR SLUG: " + resp['msg']);
                    // else {
                    //     var location = '/';
                    //     $.each(resp.slugs, function(i, s) {
                    //         if (s[1] == self.lang_default)
                    //             location = '/' + s[0];
                    //     });
                    //     window.location = location;
                    // }
                });
            }

            return def;
            // var self = this,
            //     obj = self.getMainObject(),
            //     def = $.Deferred(),
            //     $input = self.$('input[name=slug]'),
            //     slug = $input.val(),
            //     slug = $input.data('slug'),
            //     path = $('html').data('slug-path'),
            //     values = {
            //         'en_US': {
            //             'slug': 'contact.html',
            //             'new_slug': 'contact.html',
            //             'default': true},
            //         'es_ES': {
            //             'slug': 'contacto.html',
            //             'new_slug': 'contacto.html',
            //             'default': false}};

            // $.getJSON("/website_url_friendly/save_slugs", {
            //     'values': JSON.stringify(values),
            //     'path': path,
            //     'model': obj.model,
            //     'model_id': obj.id
            // }, function(resp) {
            //     console.log('yeso');
            //     // if (resp['action'] == 'none')
            //     //     return def.resolve(true);
            //     // else if (resp['action'] == 'home')
            //     //     return window.location = '/';
            //     // else if (resp['action'] == 'error')
            //     //     return alert("ERROR SLUG: " + resp['msg']);
            //     // else {
            //     //     var location = '/';
            //     //     $.each(resp.slugs, function(i, s) {
            //     //         if (s[1] == self.lang_default)
            //     //             location = '/' + s[0];
            //     //     });
            //     //     window.location = location;
            //     // }
            // });

            // // self.slug_widget.check_all(slug_checked).then(function() {
            // //     $.getJSON("/website_url_friendly/save_slugs", {
            // //         'new_slugs': JSON.stringify(slug_checked),
            // //         'path': path,
            // //         'model': obj.model,
            // //         'model_id': obj.id
            // //     }, function(resp) {
            // //         if (resp['action'] == 'none')
            // //             return def.resolve(true);
            // //         else if (resp['action'] == 'home')
            // //             return window.location = '/';
            // //         else if (resp['action'] == 'error')
            // //             return alert("ERROR SLUG: " + resp['msg']);
            // //         else {
            // //             var location = '/';
            // //             $.each(resp.slugs, function(i, s) {
            // //                 if (s[1] == self.lang_default)
            // //                     location = '/' + s[0];
            // //             });
            // //             window.location = location;
            // //         }
            // //     });
            // // }).fail(function () { def.reject(); });

            // return def;
        },
        slugChanged: function () {
            var self = this;

            setTimeout(function () {
                var url = self.$(
                    'input[name=slug][data-lang_default=true]').val();
                self.htmlPage.changeUrl(url);
                self.renderPreview();
            }, 0);
        },
        loadMetaData: function () {
            var self = this;
            var def = $.Deferred();

            self._super().then(function(data) {
                $.getJSON("/website_url_friendly/get_langs", {}, function(data) {
                    self.langs = data;
                    self.lang_default = null;

                    $.each(self.langs, function (i, l) {
                        if (l.default) {
                            self.lang_default = l.lang;
                        }
                    })

                    self.loadSlug().then(function(data_slug) {
                        def.resolve(data);
                    }).fail(function () { def.reject(); });
                });
            }).fail(function () { def.reject(); });

            return def;
        },
        saveMetaData: function(data) {
            var self = this,
                def = $.Deferred();

            self._super(data).then(function(res) {
                self.saveSlug().then(function(res_slug) {
                    def.resolve(res);
                }).fail(function () { def.reject(); });
            }).fail(function () { def.reject(); });

            return def;
        },

    });

    website.seo.Slugs = openerp.Widget.extend({
        template: 'website_url_friendly.slug_form',
        events: {
            'closed.bs.alert': 'destroy',
        },
        init: function(parent, slug) {
            var self = this;

            self.parent = parent;
            self.protocol = window.location.protocol;
            self.host = window.location.host;
            self.slug = slug;
            self._super();
        },
        start: function () {
            var self = this;
            var def = $.Deferred();
            var obj = self.parent.getMainObject();

            self._super();
            // self.$('button').on('click', function(e) {
            //     if(!self.obj) {
            //         self.def.reject();

            //         return self.def;
            //     }
            //     if (slug) {
            //         $.getJSON("/website_url_friendly/compute_slug", {
            //             'slug': slug,
            //             'model': obj.model,
            //             'id': obj.id,
            //             'lang': lang,
            //         }, function(resp) {
            //             def.resolve(resp.slug);
            //         });
            //     } else {
            //         def.resolve('');
            //     }
            //     $.getJSON("/website_url_friendly/get_langs", {}, function(data) {
            //         self.langs = data;
            //         self.lang_default = null;

            //         $.each(self.langs, function (i, l) {
            //             if (l.default) {
            //                 self.lang_default = l.lang;
            //             }
            //         })

            //         self.loadSlug().then(function(data_slug) {
            //             def.resolve(data);
            //         }).fail(function () { def.reject(); });
            //     })
            // });

            // self.$('button').on('click', function(e) {
            //     if(!self.obj) {
            //         self.def.reject();
            //         return self.def;
            //     }

            //     if (slug) {
            //         $.getJSON("/website_url_friendly/compute_slug", {
            //             'slug': slug,
            //             'model': obj.model,
            //             'id': obj.id,
            //             'lang': lang,
            //         }, function(resp) {
            //             def.resolve(resp.slug);
            //         });
            //     } else {
            //         def.resolve('');
            //     }

            //     return def;
            // });
            // self.$('button').on('click', function (ev) {
            //     var slug_div = $(this).closest('div.lang'),
            //         lang = $(slug_div).data('lang'),
            //         slug = $(slug_div).find('input').data('slug'),
            //         new_slug = $(slug_div).find('input').val(),
            //         loading = $(slug_div).find('.slug-loading'),
            //         slug_ok = $(slug_div).find('.slug-ok'),
            //         slug_error = $(slug_div).find('.slug-error');

            //     if (slug == new_slug) {
            //         $(slug_div).find('input').data('slug', new_slug);
            //         $(slug_div).find('input').val(new_slug);
            //         $(slug_ok).removeClass('hide');
            //         $(slug_error).addClass('hide');
            //         $(loading).addClass('hide');
            //         return;
            //     }

            //     $(slug_ok).addClass('hide');
            //     $(slug_error).addClass('hide');
            //     $(loading).removeClass('hide');
            //     self.check(new_slug, lang).then(function (slug_check) {
            //         $(slug_div).find('input').val(slug_check);
            //         $(slug_ok).removeClass('hide');
            //         $(slug_error).addClass('hide');
            //         $(loading).addClass('hide');
            //     }).fail(function () {
            //         $(slug_ok).addClass('hide');
            //         $(slug_error).removeClass('hide');
            //         $(loading).addClass('hide');
            //     });
            // });
        },
        // check: function(slug, lang) {
        //     var self = this,
        //         def = $.Deferred(),
        //         obj = self.parent.getMainObject();

        //     if (!obj) {
        //         def.reject();
        //         return def;
        //     }

        //     if (slug) {
        //         $.getJSON("/website_url_friendly/compute_slug", {
        //             'slug': slug,
        //             'model': obj.model,
        //             'id': obj.id,
        //             'lang': lang,
        //         }, function(resp) {
        //             def.resolve(resp.slug);
        //         });
        //     } else {
        //         def.resolve('');
        //     }

        //     return def;
        // },
        // check_all: function(slug_checked, divs_slugs, def) {
        //     var self = this,
        //         def = (typeof def == 'undefined') ? $.Deferred() : def;

        //     if (typeof divs_slugs == 'undefined') {
        //         divs_slugs = [];
        //         self.$('div.lang').each(function(i, d) {
        //             divs_slugs.push(d);
        //         });

        //     }
        //     if (divs_slugs.length == 0) {
        //         def.resolve(true);
        //     } else {
        //         var div = divs_slugs.pop(),
        //             lang = $(div).data('lang'),
        //             now = $(div).find('input').data('slug'),
        //             s = $(div).find('input').val();

        //         if (s == now) {
        //             self.check_all(slug_checked, divs_slugs, def);
        //         } else {
        //             self.check(s, lang).then(function(slug_check) {
        //                 slug_checked.push({'lang': lang, 'slug': slug_check});
        //                 self.check_all(slug_checked, divs_slugs, def);
        //             });
        //         }
        //     }

        //     return def;
        // },
    });
})();
