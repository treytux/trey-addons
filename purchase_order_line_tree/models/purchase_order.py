###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, models


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    @api.multi
    def action_view_lines(self):
        action = self.env.ref(
            'purchase_order_line_tree.purchase_order_line_tree_action')
        result = action.read()[0]
        result['context'] = {}
        order_lines = self.mapped('order_line')
        if not order_lines:
            return False
        result['domain'] = "[('id','in',%s)]" % order_lines.ids
        return result
