###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models


class StockMove(models.Model):
    _inherit = 'stock.move'

    def _search_picking_for_assignation(self):
        picking = super()._search_picking_for_assignation()
        if not picking:
            return picking
        picking_moves_sale_line_fsm = (
            picking.move_ids_without_package.mapped(
                'sale_line_id.sale_line_fsm_id'))
        if self.sale_line_id.sale_line_fsm_id == picking_moves_sale_line_fsm:
            return picking
        return self.env['stock.picking'].browse()
