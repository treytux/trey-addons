###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    @api.model
    def _search_get_detail(self, website, order, options):
        res = super()._search_get_detail(website, order, options)
        domain = res['base_domain']
        location_id = options.get('product_location')
        if not location_id:
            return res
        product_tmpl_ids = self.env['stock.quant'].search([
            ('location_id', '=', options.get('product_location')),
        ]).mapped('product_id.product_tmpl_id.id')
        if location_id:
            domain.append([('id', 'in', product_tmpl_ids)])
        return res
