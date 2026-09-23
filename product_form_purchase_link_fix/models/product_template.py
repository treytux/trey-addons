###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    def action_view_po(self):
        res = super().action_view_po()
        res['domain'] = [('product_id', 'in', self.product_variant_ids.ids)]
        return res
