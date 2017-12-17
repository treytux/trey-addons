# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.

import openerp
import re
import werkzeug

from openerp.http import request
from openerp.osv import orm
from openerp.addons.website.models.website import slugify
from urlparse import urlparse


def slugify_friendly(s):
    # TODO: Keep final slug less than 2048 characters to be safe on IE
    # Well formated slug: path/to/page.extension
    # Sample: woman/shoes/leather-boots.html
    path, extension = s[:s.rfind('.')], s[s.rfind('.'):]
    path_splits = [slugify(p or '') for p in path.split('/')]
    slug = '%s%s' % ('/'.join(path_splits), extension)

    return slug


class SlugManager(orm.AbstractModel):
    _inherit = 'ir.http'

    FORBIDDEN_NAMES = [
        'logo.png',
        'longpolling',
        'usr',
        'web']
    FORBIDDEN_PATHS = [
        '/',
        '/blog',
        '/page/homepage',
        '/page/themes',
        '/shop',
        '/shop/product',
        '/shop/category']

    _cache_expressions = {}

    def _dispatch(self):
        # TODO: Refactoring
        try:
            self._find_handler()
            return super(SlugManager, self)._dispatch()
        except werkzeug.exceptions.NotFound:
            pass

        rerouting = (
            hasattr(request, 'rerouting') and len(request.rerouting) > 0)
        if rerouting:
            return super(SlugManager, self)._dispatch()

        env = request.env
        website = env['website'].get_current_website()
        langs = [lg[0] for lg in website.get_languages()]
        path_info, lang = self._extract_slug(
            request.httprequest.path, website, langs)
        if path_info in SlugManager.FORBIDDEN_NAMES:
            return super(SlugManager, self)._dispatch()

        result = self._get_slug(path_info, lang, website.default_lang_code)
        if result is None:
            return super(SlugManager, self)._dispatch()

        return result

    def _postprocess_args(self, arguments, rule):
        processing = super(SlugManager, self)._postprocess_args(
            arguments, rule)
        parsed_url = None
        if processing and processing.status_code == 301:
            parsed_url = urlparse(processing.location)

        return self.reroute(parsed_url.path) if parsed_url else processing

    def _get_path_ids(self, expression, path):
        # TODO: Refactoring
        expression = unicode(expression)
        if expression not in SlugManager._cache_expressions:
            count = 0
            count_slug = 0
            slugs = []

            while True:
                if expression.find('<id>') != -1:
                    id0, id1 = ('id%s' % count, 'id%s' % (count + 1))
                    re_id = r'([^/]*-(?P<%s>\d+))?(?P<%s>\d+)?' % (id0, id1)
                    expression = expression.replace('<id>', re_id, 1)
                    count += 2
                    slugs.append((id0, id1))
                elif expression.find('<slug>') != -1:
                    slug = 'slug%s' % count_slug
                    re_id = r'(?P<%s>[a-zA-Z0-9\-]+)' % slug
                    expression = expression.replace('<slug>', re_id, 1)
                    count_slug += 1
                    slugs.append(slug)
                else:
                    break
            expression = r"^(?:/[^/]+)?%s$" % expression
            SlugManager._cache_expressions[expression] = (
                slugs, re.compile(expression))
        slugs, reexp = SlugManager._cache_expressions[expression]
        m = reexp.search(path)
        if not m:
            return None
        rets = []
        for part in slugs:
            if isinstance(part, tuple):
                id1 = m.group(part[0])
                id2 = m.group(part[1])

                rets.append(int(id1) if id1 else int(id2) if id2 else None)
            else:
                rets.append(m.group(part))
        return rets

    def _extract_slug(self, path, website=None, langs=None):
        website = website or request.website
        langs = langs or [lg[0] for lg in website.get_languages()]

        path_splits = path.split('/')
        valid, lang = self._check_valid_lang(path_splits[1], langs=langs)
        if valid:
            path = '/%s' % '/'.join(path_splits[2:])
            slug, _ = self._extract_slug(path, website, langs)
            return slug, lang
        else:
            path = '/'.join(path_splits[1:])
            return path, website.default_lang_code

    def _get_slug(self, name, lang, lang_default):
        env = request.env

        slug = None
        ctx = request.context.copy()
        ctx['lang'] = lang
        slug_obj = env['website_seo_url.slug']
        slugs = slug_obj.with_context(ctx).search([('name', '=', name)])
        if len(slugs) > 0:
            path = slugs[0]['path']
            request.lang = lang
            request.context['lang'] = lang
            if lang != lang_default:
                path = '/%s%s' % (lang, path)
            slug = self.reroute(path)

        return slug

    def _check_valid_lang(self, lang, langs=None):
        env = request.env

        valid_lang = False, lang
        website = env['website'].get_current_website()
        langs = langs or [lg[0] for lg in website.get_languages()]
        if lang in langs:
            valid_lang = True, lang

        return valid_lang

    def _check_valid_slug(self, slug, website, langs=None):
        valid_slug = True
        langs = langs or [lg[0] for lg in website.get_languages()]
        path = '/' + slug
        path, lang = self._extract_slug(path, website, langs)

        if path in SlugManager.FORBIDDEN_NAMES:
            valid_slug = False

        if not self._check_valid_lang(lang, langs=langs):
            valid_slug = False

        return valid_slug

    def _compute_slug(self, slugtext, model, id, lang):
        def _add_prefix(txt):
            txt_parts = txt.split('-')
            prefix = 1
            if len(txt_parts) > 1 and txt_parts[-1].isdigit():
                prefix = int(txt_parts[-1]) + 1
                txt_parts = '-'.join(txt_parts[0:-1])
            elif len(txt_parts) > 1:
                txt_parts = '-'.join(txt_parts)
            else:
                txt_parts = ''.join(txt_parts)
            return '%s-%s' % (txt_parts, prefix)

        context = request.context.copy()
        context['lang'] = lang

        urls = self.routing_map().bind_to_environ(request.httprequest.environ)
        if urls.test(slugtext):
            return self._compute_slug(_add_prefix(slugtext), model, id, lang)

        Slug = request.registry['website_seo_url.slug']
        slugs = Slug.search(request.cr, openerp.SUPERUSER_ID,
                            [('name', '=', slugtext)], context=context)
        if len(slugs) > 0:
            return self._compute_slug(_add_prefix(slugtext), model, id, lang)

        return slugtext

    def url_for(self, url):
        Slug = request.registry['website_seo_url.slug']

        o = urlparse(url)
        path = o.path

        def _find_slug(slug, lang):
            context = request.context.copy()
            context['lang'] = lang

            slugs = Slug.search_read(request.cr, openerp.SUPERUSER_ID,
                                     [('path', '=', slug)], ['name'],
                                     context=context)
            if len(slugs) == 0:
                return None

            if lang != request.website.default_lang_code:
                url = '/%s/%s' % (lang, slugs[0]['name'])
            else:
                url = '/%s' % slugs[0]['name']

            if o.query:
                url += '?%s' % o.query

            if o.fragment:
                url += '#' + o.fragment

            return url

        _, lang = self._extract_slug(path, website=request.website)

        compute_path = self._compute_path(path)
        slug_found = _find_slug(compute_path, lang)

        if slug_found:
            return slug_found

        return url

    def _compute_path(self, path):
        env = request.env
        website = env['website'].get_current_website()
        lang_prefix = (
            '' if request.lang == website.default_lang_code else
            '/%s' % request.lang)

        # Slicing setting directly the pattern (no var stored) is the fastest
        # method to search than find and startswith
        if (path[:len('%s/page/' % lang_prefix)] ==
           '%s/page/' % lang_prefix):
            ids = self._get_path_ids('/page/<slug>', path)
            if ids:
                # Percentage replacement is faster than format method
                return '/page/%s' % ids[0]

            ids = self._get_path_ids(r'/page/website\.<slug>', path)
            if ids:
                return '/page/%s' % ids[0]

        if (path[:len('%s/blog/' % lang_prefix)] ==
           '%s/blog/' % lang_prefix):
            ids = self._get_path_ids('/blog/<slug>/post/<slug>', path)
            if ids:
                return '/blog/%s/post/%s' % (ids[0], ids[1])

            ids = self._get_path_ids('/blog/<id>/post/<id>', path)
            if ids:
                return '/blog/%s/post/%s' % (ids[0], ids[1])

            ids = self._get_path_ids('/blog/<slug>', path)
            if ids:
                return '/blog/%s' % ids[0]

            ids = self._get_path_ids('/blog/<id>', path)
            if ids:
                return '/blog/%s' % ids[0]

            ids = self._get_path_ids('/blog/<slug>/tag/<slug>', path)
            if ids:
                return '/blog/%s/tag/%s' % (ids[0], ids[1])

            ids = self._get_path_ids('/blog/<id>/tag/<id>', path)
            if ids:
                return '/blog/%s/tag/%s' % (ids[0], ids[1])

        if (path[:len('%s/shop/' % lang_prefix)] ==
           '%s/shop/' % lang_prefix):
            ids = self._get_path_ids('/shop/product/<slug>', path)
            if ids:
                return '/shop/product/%s' % ids[0]

            ids = self._get_path_ids('/shop/product/<id>', path)
            if ids:
                return '/shop/product/%s' % ids[0]

            ids = self._get_path_ids('/shop/category/<slug>', path)
            if ids:
                return '/shop/category/%s' % ids[0]

            ids = self._get_path_ids('/shop/category/<id>', path)
            if ids:
                return '/shop/category/%s' % ids[0]

        return path
