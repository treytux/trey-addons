###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from datetime import datetime

from odoo import _, api, fields, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    cancelled_date = fields.Date(
        string='Cancelled date')

    @api.multi
    def action_cancel(self):
        res = super().action_cancel()
        self.cancelled_date = datetime.now().date()
        return res

    @api.multi
    def get_order_status_info(self):
        status_list = []
        product_uom_qty_total = 0
        qty_delivered_total = 0
        if self.date_order:
            status_list.append((self.date_order, _('Received order')))
        if self.transaction_ids:
            transaction = self.env['payment.transaction'].search([
                ('sale_order_ids', '=', self.id),
            ], order='date desc', limit=1)
            if transaction:
                if transaction.state == 'done':
                    msg = _('Payment accepted with: %s' %
                            transaction.acquirer_id.name)
                elif transaction.state == 'cancel':
                    msg = _('Payment cancelled')
                else:
                    msg = _('Waiting for payment confirmation from: %s' %
                            transaction.acquirer_id.name)
                status_list.append((transaction.date, msg))
        if self.confirmation_date:
            status_list.append((self.confirmation_date, _('Confirmed order')))
        if self.order_line:
            for line in self.order_line:
                product_uom_qty_total = (
                    product_uom_qty_total + line.product_uom_qty)
                qty_delivered_total = qty_delivered_total + line.qty_delivered
            stock_picking_done = self.picking_ids.filtered(
                lambda p: p.state == 'done')
            if (
                    qty_delivered_total < product_uom_qty_total
                    and qty_delivered_total > 0
            ):
                status_list.append((
                    stock_picking_done[0].date_done,
                    _('Partially shipped order')))
            elif qty_delivered_total == product_uom_qty_total:
                status_list.append((
                    stock_picking_done[0].date_done, _('Shipped order')))
        if self.state == 'cancel':
            status_list.append((self.cancelled_date, _('Cancelled order')))
        return status_list
