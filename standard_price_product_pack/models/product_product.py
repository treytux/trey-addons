###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models


class ProductProduct(models.Model):
    _inherit = 'product.product'

    def write(self, vals):
        res = super().write(vals)
        if not vals.get('standard_price', False):
            return res
        related_packs = self.search([
            ('pack_line_ids.product_id', '=', self.id),
        ]).mapped('product_tmpl_id')
        if related_packs:
            related_packs._compute_standard_price()
        return res
