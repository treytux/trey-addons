###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import logging

from odoo import fields, http
from odoo.addons.website_sale.controllers.main import WebsiteSale
from odoo.http import request
from psycopg2 import IntegrityError

_logger = logging.getLogger(__name__)


class WebsiteSale(WebsiteSale):
    @http.route()
    def product(self, product, category='', search='', **kwargs):
        product_view = request.env['website.sale.product.view'].search([
            ('session_id', '=', request.session.sid),
            ('product_id', '=', product.id),
        ], limit=1)
        if not product_view:
            try:
                with request.env.cr.savepoint():
                    product_view = request.env[
                        'website.sale.product.view'].create({
                            'session_id': request.session.sid,
                            'product_id': product.id,
                        })
            except IntegrityError:
                _logger.error(
                    'Couldn\'t save the product view record for session_id %s'
                    'and product_id %s', request.session.sid, product.id)
        else:
            product_view.last_view_datetime = fields.Datetime.now()
        return super().product(
            product=product, category=category, search=search, **kwargs)
