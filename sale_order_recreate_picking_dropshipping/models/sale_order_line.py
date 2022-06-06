###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, models


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    @api.multi
    def _get_qty_procurement(self):
        purchase_lines_sudo = self.sudo().purchase_line_ids
        purchase_lines_not_cancel = purchase_lines_sudo.filtered(
            lambda ln: ln.state != 'cancel')
        if purchase_lines_not_cancel:
            qty = 0.0
            for po_line in purchase_lines_not_cancel:
                sale_lines = self.env['sale.order.line'].search([
                    ('purchase_line_ids', '=', po_line.id),
                ])
                for move in sale_lines.move_ids:
                    if move.state == 'cancel':
                        continue
                    if move.location_id.usage == 'supplier':
                        qty += po_line.product_uom._compute_quantity(
                            move.product_uom_qty, self.product_uom,
                            rounding_method='HALF-UP')
                    if move.location_dest_id.usage == 'supplier':
                        qty -= po_line.product_uom._compute_quantity(
                            move.product_uom_qty, self.product_uom,
                            rounding_method='HALF-UP')
            return qty
        else:
            return super()._get_qty_procurement()
