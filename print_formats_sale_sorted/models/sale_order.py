###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from collections import OrderedDict

from odoo import api, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.multi
    def get_lines_sorted(self):
        self.ensure_one()
        lines_dict = {}
        for line in self.order_line:
            attrs = line.product_id.attribute_value_ids.mapped(
                'attribute_id')
            key = '%s' % (line.product_id.website_default_code or 'z')
            for attr in attrs:
                filtered_val = line.product_id.attribute_value_ids.filtered(
                    lambda x: x.attribute_id.id == attr.id)
                key += '-%s' % str(filtered_val.sequence).zfill(4)
            key += '-%s' % str(line.id).zfill(4)
            lines_dict.setdefault(key, line)
        return OrderedDict(sorted(lines_dict.items())).values()
