# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import api, models


class ProductProduct(models.Model):
    _inherit = 'product.product'

    @api.model
    def get_sorted_attribute_values(self):
        return ([att for att in self.attribute_value_ids
                if att.attribute_id.type != 'color'][0],
                [att for att in self.attribute_value_ids
                if att.attribute_id.type == 'color'][0])
