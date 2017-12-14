# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.
import json
from openerp.http import request
from openerp.addons.web import http
from openerp.addons.website_url_friendly.models.ir_http import slugify_friendly
import logging
_log = logging.getLogger(__name__)


class UrlFriendly(http.Controller):
    def _parse_slug(self, slug):
        return slugify_friendly(slug.strip())

    def _langs(self):
        default_lang_code = request.website.default_lang_code
        langs = request.website.get_languages()

        return default_lang_code, langs

    @http.route(['/website_url_friendly/get_langs'],
                type='http', auth='user', website=True)
    def get_langs(self):
        default, langs = self._langs()
        data = [{'lang': l[0], 'default': l[0] == default}
                for l in langs]
        return json.dumps(data)

    @http.route(['/website_url_friendly/compute_slug'],
                type='http', auth='user', website=True)
    def compute_slug(self, slug, model, id, lang):
        env = request.env
        irh = env['ir.http']

        slug = self._parse_slug(slug)
        if not irh.check_valid_slug(slug, request.website):
            slug += "-1"

        compute = irh.compute_slug(slug, model, id, lang)

        return json.dumps(
            {'slug': compute, 'model': model, 'id': id, 'lang': lang})

    @http.route(['/website_url_friendly/load'],
                type='http', auth='user', website=True)
    def load_slug(self, path, model, model_id):
        env = request.env

        data = None
        if path in request.registry['ir.http'].FORBIDDEN_PATHS:
            return json.dumps(data)

        slug_obj = env['website_url_friendly.slug']
        irh = env['ir.http']
        computed_path = irh.compute_path(path)
        current_lang_code = request.context['lang']
        default_lang_code = request.website.default_lang_code
        slug = slug_obj.search(
            [('path', '=', computed_path)])
        data = {
            'default_lang_code': (
                current_lang_code == default_lang_code),
            'lang_code': current_lang_code,
            'name': slug[0].name if slug else ''}

        return json.dumps(data)

    # @http.route(['/website_url_friendly/load'],
    #             type='http', auth='user', website=True)
    # def load_slug(self, path, model, model_id):
    #     env = request.env

    #     if path in request.registry['ir.http'].FORBIDDEN_PATHS:
    #         return json.dumps({'empty': True})

    #     ctx = request.context.copy()
    #     slug_obj = env['website_url_friendly.slug']
    #     irh = env['ir.http']
    #     computed_path = irh.compute_path(path)
    #     data = []
    #     default_lang_code = request.website.default_lang_code
    #     for l in request.website.get_languages():
    #         ctx['lang'] = l[0]
    #         slug = slug_obj.with_context(ctx).search(
    #             [('path', '=', computed_path)])
    #         data.append({'lang': ctx['lang'],
    #                      'lang_default': ctx['lang'] == default_lang_code,
    #                      'name': slug[0].name if slug else ''})
    #     return json.dumps({'empty': False, 'slugs': data})

    @http.route(['/website_url_friendly/save_slugs'],
                type='http', auth='user', website=True)
    def save_slugs(self, new_slug, path, model, model_id):
        env = request.env
        current_lang_code = request.context['lang']
        default_lang_code = request.website.default_lang_code

        if path in request.registry['ir.http'].FORBIDDEN_PATHS:
            return json.dumps({'errors': [
                "Sorry, this URL can't be used. Please try another one."]})

        slug_obj = env['website_url_friendly.slug']
        slug = slug_obj.search([('path', '=', path)])
        irh = env['ir.http']
        new_slug = json.loads(new_slug)

        if (new_slug['new_name'] == '' and not slug):
            return json.dumps({})

        if (new_slug['new_name'] == '' and slug):
            # TODO: unlink slugs just if current_lang_code == default_lang_code
            # in any other case asign current slug the default slug name
            redirect = slug.path
            slug.sudo().unlink()
            return json.dumps({'redirect': redirect})

        name = irh.compute_slug(
            self._parse_slug(new_slug['new_name']),
            model, model_id, request.lang)
        slug_data = {
            'name': name, 'path': path, 'model': model,
            'model_id': model_id}
        if slug:
            # TODO: if slug was created from not default_lang_code, prevent
            # when update default lang slug to asign this translation to
            # the previous one
            # 1. Create slug 'contacto' in 'es_ES' for '/page/contactus'
            # 2. Update slug 'contact' in 'en_US' (default_language) for
            # '/page/contactus'
            # 3. Both slugs are now:
            # '/contact' for English
            # '/es_ES/contact' for Spanish
            # 4. We have to keep '/es_ES/contacto' for Spanish
            slug.sudo().write(slug_data)
        else:
            slug = slug_obj.sudo().create(slug_data)

        redirect = (
            '/%s%s' % (
                ('' if
                 current_lang_code == default_lang_code else
                 '%s/' % current_lang_code), slug.name))
        data = {'slug': {
            'default_lang_code': (
                current_lang_code == default_lang_code),
            'lang_code': current_lang_code,
            'name': slug.name if slug else ''},
            'redirect': redirect}

        return json.dumps(data)
        # redirect
        # irh = env['ir.http']
        # ctx = request.context.copy()
        # default_lang, langs = self._langs()
        # model_id = int(model_id)

        # if path in request.registry['ir.http'].FORBIDDEN_PATHS:
        #     return json.dumps({'empty': True})

        # values = json.loads(values)
        # if len(values) == 0:
        #     _log.info('=' * 30)
        #     _log.info('eliminar')
        #     _log.info('=' * 30)
        # # for s in values:
        # #     if s['lang'] not in [l[0] for l in langs]:
        # #         return json.dumps({
        # #             'action': 'error',
        # #             'msg': u'Invalid language: %s.' % s['lang']})

        # # unlink_slugs = (
        # #     len([s for s in values if s['slug'] == u'']) == len(values))
        # _log.info('=' * 30)
        # _log.info(('values', values))
        # _log.info(('values', values['en_US']))
        # _log.info('=' * 30)
        # return json.dumps({'action': 'none'})
        # slug_obj = env['website_url_friendly.slug']
        # slugs = slug_obj.search([('path', '=', path)])
        # if slugs and unlink_slugs:
        #     slugs[0].sudo().unlink()
        #     # Model.write(request.cr, request.uid, [id], {'slug_id': False})
        #     return json.dumps({'action': 'home'})

        # # primero el idioma por defecto
        # for s in values:
        #     for i, l in enumerate(langs):
        #         if l[0] == s['lang']:
        #             s['id'] = i
        # values.sort(key=lambda s: s['id'])

        # # guardamos en los lenguajes indicados
        # return_slugs = []
        # for s in values:
        #     name = self._parse_slug(s['slug'])
        #     lang = s['lang']
        #     ctx['lang'] = lang

        #     name = irh.compute_slug(name, model, model_id, lang)

        #     data = {'name': name, 'path': path, 'model': model,
        #             'model_id': model_id}

        #     if len(slugs) == 0:
        #         slug_obj.sudo().create(data)
        #     else:
        #         slugs.sudo().write(data)

        #     return_slugs.append((name, lang))

        # if len(return_slugs) == 0:
        #     return json.dumps({'action': 'none'})
        # else:
        #     return json.dumps({'action': 'reload', 'slugs': return_slugs})
