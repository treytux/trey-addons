# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import api, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    @api.model
    def get_sorted_attribute_lines(self):
        return ([att for att in self.attribute_line_ids
                if att.attribute_id.type != 'color'][0],
                [att for att in self.attribute_line_ids
                if att.attribute_id.type == 'color'][0])
