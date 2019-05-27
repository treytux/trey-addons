# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import api, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    @api.model
    def get_sorted_attribute_lines(self):
        not_color_lines = [
            att for att in self.attribute_line_ids
            if att.attribute_id.type != 'color']
        color_lines = [
            att for att in self.attribute_line_ids
            if att.attribute_id.type == 'color']
        if not_color_lines and color_lines:
            return (not_color_lines[0], color_lines[0])
        return False
