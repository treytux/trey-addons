###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, models


class SaleAdvancePaymentInv(models.TransientModel):
    _inherit = 'sale.advance.payment.inv'

    @api.multi
    def _create_invoice(self, order, so_line, amount):
        invoice = super()._create_invoice(
            order=order, so_line=so_line, amount=amount)
        if order.partner_group_id:
            invoice.partner_group_id = order.partner_group_id
        return invoice
