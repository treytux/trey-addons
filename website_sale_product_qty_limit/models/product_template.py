# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
import json
from openerp import api, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    @api.model
    def _get_variants_qty_limit(self):
        qty_limits = {}
        for v in self.product_variant_ids:
            qty_limits.update({v.id: v.qty_limit})
        return json.dumps(qty_limits)
