###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, models


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    @api.multi
    def do_print_picking_valued(self):
        commercial_partner_id = self.partner_id.commercial_partner_id
        if commercial_partner_id.delivery_slip_type == 'valued':
            return self.env.ref(
                'print_formats_picking_valued.'
                'report_stock_deliveryslip_valued_create'
            ).report_action(self)
        else:
            return self.env.ref(
                'stock.action_report_delivery').report_action(self)

    def get_amount_untaxed(self):
        amount_untaxed_dict = {}
        for picking in self:
            for move in picking.move_lines:
                sale_line = move.sale_line_id
                price = sale_line.price_unit * (
                    1 - (sale_line.discount or 0.0) / 100.0)
                if picking.state == 'done':
                    qty_done = sum(move.mapped('move_line_ids.qty_done'))
                else:
                    qty_done = move.product_uom_qty
                price_subtotal = sale_line.tax_id.compute_all(
                    price,
                    sale_line.order_id.currency_id,
                    qty_done,
                    product=sale_line.product_id,
                    partner=sale_line.order_id.partner_shipping_id
                )['total_excluded']
                if picking not in amount_untaxed_dict:
                    amount_untaxed_dict[picking] = 0
                amount_untaxed_dict[picking] += price_subtotal
        return amount_untaxed_dict
