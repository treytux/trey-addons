###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, models


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    def action_stock_moves(self):
        form_view = self.env.ref('stock.view_move_form')
        tree_view = self.env.ref('stock.view_move_tree')
        search_view = self.env.ref('stock.view_move_search')
        return {
            'name': _('Stock Moves'),
            'res_model': 'stock.move',
            'type': 'ir.actions.act_window',
            'views': [(tree_view.id, 'tree'), (form_view.id, 'form')],
            'view_mode': 'tree,form',
            'search_view_id': search_view.id,
            'view_type': 'form',
            'context': {
                'search_default_product_id': self.product_id.id,
                'search_default_partner_id': self.order_partner_id.id,
            },
        }
