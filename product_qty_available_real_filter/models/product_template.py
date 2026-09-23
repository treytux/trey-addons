###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    qty_available_real = fields.Float(
        search='_search_qty_available_real',
    )

    @api.model
    def _search_qty_available_real(self, operator, value):
        domain = [('qty_available_real', operator, value)]
        product_variant_ids = self.env['product.product'].search(domain)
        return [('product_variant_ids', 'in', product_variant_ids.ids)]
