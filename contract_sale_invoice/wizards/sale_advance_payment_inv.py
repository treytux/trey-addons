###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, api, models
from odoo.exceptions import UserError


class SaleAdvancePaymentInv(models.TransientModel):
    _inherit = 'sale.advance.payment.inv'

    @api.multi
    def _create_invoice(self, order, so_line, amount):
        invoice = super()._create_invoice(order, so_line, amount)
        if self.advance_payment_method == 'percentage':
            lines = order.order_line.filtered(
                lambda l: not l.is_contract and not l.is_downpayment)
            amount = sum(lines.mapped('price_subtotal')) * self.amount / 100
            lines_downpayment = order.order_line.filtered(
                lambda l: l.is_downpayment and l.id != so_line.id)
            amount_downpayment = sum(
                lines_downpayment.mapped('price_unit'))
            amount_unpaid = sum(
                lines.mapped('price_subtotal')) - amount_downpayment
            if amount > amount_unpaid:
                raise UserError(
                    _('Max amount to invoice is: %s') % amount_unpaid)
            so_line.price_unit = amount
            invoice.invoice_line_ids[0].price_unit = amount
            invoice.compute_taxes()
        return invoice
