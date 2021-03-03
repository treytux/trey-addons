###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import json

from odoo import api, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    @api.model
    def _get_variants_qty_limit(self):
        return json.dumps(
            {v.id: v.qty_limit for v in self.product_variant_ids})
