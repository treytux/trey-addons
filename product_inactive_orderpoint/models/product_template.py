###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    def product_inactive_orderpoint(self):
        for template in self:
            template.product_variant_ids.mapped('orderpoint_ids').unlink()
            template.active = False
