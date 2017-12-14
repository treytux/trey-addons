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
import logging
_log = logging.getLogger(__name__)


def slugify_friendly(s):
    # Well format slug: path/to/page.extension
    # Sample: woman/shoes/leather-boots.html
    # TODO: Keep final slug less than 2048 characters to be safe on IE

    path, extension = s[:s.rfind('.')], s[s.rfind('.'):]
    path_splits = [slugify(p or '') for p in path.split('/')]
    slug = '{}{}'.format('/'.join(path_splits), extension)

    # s = ustr(s)
    # if s[0] == u'/':
    #     s = s[1:]
    # if s[-1] == u'/':
    #     s = s[0:-1]

    # uni = unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode(
    #     'ascii')
    # slug = re.sub('[\W_]', ' ', uni).strip().lower()
    # slug = re.sub('[-\s]+', '-', slug)

    # if len(slug) == len(s):
    #     pos = [m.start() for m in re.finditer('/', s)]
    #     if len(pos) == 0:
    #         return slug

    #     slug = list(slug)
    #     for i in pos:
    #         slug[i] = s[i]

    #     slug = u"".join(slug)
    #     if slug[0] == u'/':
    #         slug = slug[1:]

    return slug


class SlugManager(orm.AbstractModel):
    _inherit = 'ir.http'

    FORBIDDEN_NAMES = ['logo.png', 'web', 'longpolling', 'usr']
    FORBIDDEN_PATHS = [u'/', u'/page/homepage', u'/page/themes']

    _cache_expressions = {}

    def _dispatch(self):
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
        path_info, lang = self.extract_slug(
            request.httprequest.path, website, langs)
        if path_info in SlugManager.FORBIDDEN_NAMES:
            return super(SlugManager, self)._dispatch()

        result = self.get_slug(path_info, lang, website.default_lang_code)
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

    def _find_ids_in_path(self, expression, path):
        expression = unicode(expression)
        if expression not in SlugManager._cache_expressions:
            count = 0
            count_slug = 0
            slugs = []

            while True:
                if expression.find('<id>') != -1:
                    id0, id1 = 'id{}'.format(count), 'id{}'.format(count + 1)
                    re_id = '([^/]*-(?P<{}>\d+))?(?P<{}>\d+)?'.format(id0, id1)
                    expression = expression.replace('<id>', re_id, 1)
                    count += 2
                    slugs.append((id0, id1))
                elif expression.find('<slug>') != -1:
                    slug = 'slug{}'.format(count_slug)
                    re_id = '(?P<{}>[a-zA-Z0-9\-]+)'.format(slug)
                    expression = expression.replace('<slug>', re_id, 1)
                    count_slug += 1
                    slugs.append(slug)
                else:
                    break
            expression = "^(?:/[^/]+)?{}$".format(expression)
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

    def extract_slug(self, path, website=None, langs=None):
        # Extract slug and language from path
        website = website or request.website
        langs = langs or [lg[0] for lg in website.get_languages()]

        path_splits = path.split('/')
        valid, lang = self.check_valid_lang(path_splits[1], langs=langs)
        if valid:
            path = u'/' + u'/'.join(path_splits[2:])
            slug, _ = self.extract_slug(path, website, langs)
            return slug, lang
        else:
            path = u'/'.join(path_splits[1:])
            return path, website.default_lang_code

    def get_slug(self, name, lang, lang_default):
        env = request.env

        slug = None
        ctx = request.context.copy()
        ctx['lang'] = lang
        slug_obj = env['website_url_friendly.slug']
        slugs = slug_obj.with_context(ctx).search([('name', '=', name)])
        if len(slugs) > 0:
            path = slugs[0]['path']
            request.lang = lang
            request.context['lang'] = lang
            if lang != lang_default:
                path = u'/{}{}'.format(lang, path)
            slug = self.reroute(path)

        return slug

    def check_valid_lang(self, lang, langs=None):
        env = request.env

        valid_lang = False, lang
        website = env['website'].get_current_website()
        langs = langs or [lg[0] for lg in website.get_languages()]
        if lang in langs:
            valid_lang = True, lang

        return valid_lang

    def check_valid_slug(self, slug, website, langs=None):
        valid_slug = True
        langs = langs or [lg[0] for lg in website.get_languages()]
        path = u'/' + slug
        path, lang = self.extract_slug(path, website, langs)

        if path in SlugManager.FORBIDDEN_NAMES:
            valid_slug = False

        if not self.check_valid_lang(lang, langs=langs):
            valid_slug = False

        return valid_slug

    def compute_slug(self, slugtext, model, id, lang):
        """ Devuelve un nombre de slug único """
        def _add_prefix(txt):
            txt_parts = txt.split('-')
            prefix = 1
            if len(txt_parts) > 1 and txt_parts[-1].isdigit():
                prefix = int(txt_parts[-1]) + 1
                txt_parts = u"-".join(txt_parts[0:-1])
            elif len(txt_parts) > 1:
                txt_parts = u"-".join(txt_parts)
            else:
                txt_parts = u"".join(txt_parts)
            return u"{}-{}".format(txt_parts, prefix)

        context = request.context.copy()
        context['lang'] = lang

        # routes registers
        urls = self.routing_map().bind_to_environ(request.httprequest.environ)
        if urls.test(slugtext):
            return self.compute_slug(_add_prefix(slugtext), model, id, lang)

        # slugs registrados
        Slug = request.registry['website_url_friendly.slug']
        slugs = Slug.search(request.cr, openerp.SUPERUSER_ID,
                            [('name', '=', slugtext)], context=context)
        if len(slugs) > 0:
            return self.compute_slug(_add_prefix(slugtext), model, id, lang)

        return slugtext

    def url_for(self, url):
        """ URL ODOO => SLUG """
        Slug = request.registry['website_url_friendly.slug']

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

            # print "   URLFOR FOUND", lang, slug, slugs

            if lang != request.website.default_lang_code:
                url = u'/{}/{}'.format(lang, slugs[0]['name'])
            else:
                url = u'/{}'.format(slugs[0]['name'])

            if o.query:
                url += u'?{}'.format(o.query)

            if o.fragment:
                url += '#' + o.fragment

            return url

        _, lang = self.extract_slug(path, website=request.website)

        # buscamos slug
        compute_path = self.compute_path(path)
        slug_found = _find_slug(compute_path, lang)

        if slug_found:
            return slug_found

        # por defecto
        return url

    def compute_path(self, path):
        """ Procesa la url de odoo antes de guardar el slug """
        if path.find('/page/') == -1:
            return path
        ids = self._find_ids_in_path('/page/<slug>', path)
        if ids:
            return u"/page/{}".format(ids[0])
        ids = self._find_ids_in_path('/page/website\.<slug>', path)
        if ids:
            return u"/page/{}".format(ids[0])
        return path
