###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from openerp import api, models
from openerp.http import request


class Website(models.Model):
    _inherit = 'website'

    @api.multi
    def recently_viewed_products(self):
        return request.env['website.sale.product.view'].search([
            ('session_id', '=', request.session.sid)], limit=6)

    @api.multi
    def get_product_variant(self, viewed_product):
        combination_info = viewed_product.product_id._get_combination_info()
        return viewed_product.product_id.env['product.product'].browse(
            combination_info['product_id'])
