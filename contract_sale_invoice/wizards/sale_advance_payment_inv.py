###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models, api


class SaleAdvancePaymentInv(models.TransientModel):
    _inherit = 'sale.advance.payment.inv'

    @api.multi
    def _create_invoice(self, order, so_line, amount):
        invoice = super()._create_invoice(order, so_line, amount)
        if self.advance_payment_method == 'percentage':
            lines = order.order_line.filtered(
                lambda l: not l.is_contract and not l.is_downpayment)
            amount = sum(lines.mapped('price_subtotal')) * self.amount / 100
            so_line.price_unit = amount
            invoice.invoice_line_ids[0].price_unit = amount
            invoice.compute_taxes()
        return invoice
