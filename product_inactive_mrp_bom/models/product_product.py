###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, models


class ProductProduct(models.Model):
    _inherit = 'product.product'

    def write(self, vals):
        if 'active' not in vals:
            return super().write(vals)
        if vals['active'] is False:
            msg = _('Bill of materials automatically deactivated when '
                    'deactivating the product.')
            for product in self:
                variants = product.product_tmpl_id.product_variant_ids - product
                cond = (
                    not variants
                    or variants.mapped('active') == [False]
                    or product.product_tmpl_id.active is False)
                if cond:
                    boms = self.env['mrp.bom'].search([
                        ('product_tmpl_id', '=', product.product_tmpl_id.id),
                    ])
                else:
                    boms = self.env['mrp.bom'].search([
                        ('product_id', '=', product.id),
                    ])
                for bom in boms:
                    bom.active = False
                    bom.message_post(body=msg)
        return super().write(vals)
