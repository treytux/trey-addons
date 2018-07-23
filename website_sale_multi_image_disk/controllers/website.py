# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp.addons.web import http
from openerp.http import request
from openerp.addons.website.controllers import main
from openerp.addons.website_sale_multi_image_disk import (
    multi_image_disk_tools as midt)
import logging
_log = logging.getLogger(__name__)


class Website(main.Website):
    @http.route()
    def website_image(self, model, id, field, max_width=None, max_height=None):
        if model not in ('product.template', 'product.product'):
            return super(Website, self).website_image(
                model, id, field, max_width=max_width, max_height=max_height)
        assert field in ('image', 'image_big', 'image_medium', 'image_small')
        try:
            idsha = id.split('_')
            id = int(idsha[0])
            translate = request.env['ir.config_parameter'].get_param(
                'website_sale_multi_image_disk.translate') == 'True'
            product = request.env[model].with_context(
                lang=(
                    translate and
                    request.lang or
                    request.website.default_lang_code)).browse(id)
            if not product:
                _log.error('Product %s not found requesting image', id)
                return None
            return product._get_default_disk_image(
                field=field, max_width=max_width, max_height=max_height)
        except Exception as e:
            _log.error('Requesting image for product %s, error: %s', id, e)
            return None

    @http.route([
        '/website/image/<slug>',
        '/website/image/<int:max_width>x<int:max_height>/<slug>'],
        auth='public', website=True, multilang=False)
    def website_disk_image(self, slug, max_width=None, max_height=None):
        return midt.get_disk_image(
            slug, max_width=max_width, max_height=max_height)
