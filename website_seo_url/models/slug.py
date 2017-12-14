# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.

from openerp.http import request
from openerp import api, models, fields
from openerp.addons.website_seo_url.models.ir_http import slugify_friendly


class Slug(models.Model):
    _name = 'website_seo_url.slug'

    name = fields.Char(
        string=u'Slug',
        required=True,
        translate=True)
    path = fields.Char(
        string=u'Permalink',
        required=True,
        translate=False)
    model = fields.Char(
        string=u'Model',
        required=True,
        translate=False)
    model_id = fields.Integer(
        string=u'Model Id',
        required=True)

    _sql_constraints = [
        ('name_unique', 'unique (name)', u'The Slug must be unique!'),
        ('path_unique', 'unique (path)', u'The Permalink must be unique!')]

    @api.model
    def load_slug(self, path, website_context):
        env = request.env

        irh = env['ir.http']
        if path in irh.FORBIDDEN_PATHS:
            return None

        website = env['website'].get_current_website()
        slug = self.with_context(website_context).search(
            [('path', '=', irh._compute_path(path))])

        return {
            'default_lang_code': (
                website_context['lang'] == website.default_lang_code),
            'lang_code': website_context['lang'],
            'name': slug[0].name if slug else ''}

    @api.model
    def _parse_slug(self, slug):
        return slugify_friendly(slug.strip())

    @api.model
    def save_slug(self, new_slug, path, model, model_id, website_context):
        env = request.env

        website = env['website'].get_current_website()
        current_lang_code = website_context['lang']
        default_lang_code = website.default_lang_code

        if path in request.registry['ir.http'].FORBIDDEN_PATHS:
            return {'errors': [
                "Sorry, this URL can't be used. Please try another one."]}

        slug = self.with_context(website_context).search([('path', '=', path)])
        irh = env['ir.http']

        if (new_slug == '' and not slug):
            return {}

        if (new_slug == '' and slug):
            # TODO: unlink slugs just if current_lang_code == default_lang_code
            # in any other case asign current slug the default slug name
            redirect = slug.path
            slug.unlink()
            return {'redirect': redirect}

        name = irh._compute_slug(
            self._parse_slug(new_slug),
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
            slug.write(slug_data)
        else:
            slug = self.with_context(website_context).create(slug_data)

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

        return data
