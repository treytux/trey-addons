###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from collections import OrderedDict

from odoo import models


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def get_move_lines_sorted(self, picking):
        if self.env.context.get('is_operations'):
            move_objs = picking.move_ids_without_package.mapped(
                'move_line_ids')
        else:
            move_objs = (
                (picking.move_line_ids and picking.state == 'done')
                and picking.move_line_ids
                or picking.move_lines.filtered(lambda x: x.product_uom_qty)
            )
        move_objs_dict = {}
        for move in move_objs:
            attrs = move.product_id.attribute_value_ids.mapped(
                'attribute_id')
            key = '%s' % (move.product_id.website_default_code or 'z')
            for attr in attrs:
                filt_val = move.product_id.attribute_value_ids.filtered(
                    lambda x: x.attribute_id.id == attr.id)
                key += '-%s' % str(filt_val.sequence).zfill(4)
            key += '-%s' % str(move.id).zfill(4)
            move_objs_dict.setdefault(key, move)
        return OrderedDict(sorted(move_objs_dict.items())).values()
