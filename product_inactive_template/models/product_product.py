###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, models


class ProductProduct(models.Model):
    _inherit = 'product.product'

    @api.multi
    def write(self, vals):
        if self._context.get('ignore_inactive'):
            return super().write(vals)
        if 'active' not in vals:
            return super().write(vals)
        if vals['active'] is False:
            other_variants = self.product_tmpl_id.product_variant_ids - self
            cond = (
                not other_variants
                or other_variants.mapped('active') == [False])
            if cond:
                self.product_tmpl_id.active = False
        return super().write(vals)
