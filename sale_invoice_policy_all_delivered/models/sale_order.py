###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    invoice_policy = fields.Selection(
        selection_add=[
            ('all_delivered', 'All delivered'),
        ],
    )

    def _check_pendding_moves(self):
        not_delivered_lines = self.order_line.filtered(
            lambda ln: not ln.is_delivery and ln.product_uom_qty > 0
            and ln.product_id.type != 'service'
            and ln.qty_delivered < ln.product_uom_qty)
        for line in not_delivered_lines:
            cancel_moves = line.move_ids.filtered(lambda m: m.state == 'cancel')
            if not cancel_moves:
                return 'no'
        lines_to_invoice = self.order_line.filtered(
            lambda ln: not ln.is_delivery
            and ((ln.qty_delivered > ln.qty_invoiced
                  and ln.product_id.type != 'service')
                 or (ln.product_uom_qty > ln.qty_invoiced
                     and ln.product_id.type == 'service')))
        if not lines_to_invoice:
            return 'no'
        return 'to invoice'

    def _get_invoiced(self):
        res = super()._get_invoiced()
        for sale in self:
            if sale.invoice_policy != 'all_delivered':
                continue
            if not sale.picking_ids :
                sale.invoice_status = 'no'
                return res
            lines = sale.order_line.filtered(
                lambda ln: not ln.is_delivery
                and ln.product_id.type != 'service')
            qty_request = sum([line.product_uom_qty for line in lines])
            qty_delivered = sum([line.qty_delivered for line in lines])
            qty_invoiced = sum([line.qty_invoiced for line in lines])
            to_invoice = (
                qty_delivered == qty_request and qty_request > 0
                and qty_invoiced == 0)
            no_invoice = (
                qty_delivered >= 0 and qty_delivered < qty_request
                and qty_request > 0 and qty_invoiced == 0)
            if to_invoice:
                sale.invoice_status = 'to invoice'
            elif no_invoice:
                sale.invoice_status = sale._check_pendding_moves()
            elif qty_invoiced > 0:
                continue
        return res
