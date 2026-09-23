###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class SaleAdvancePaymentInv(models.TransientModel):
    _inherit = 'sale.advance.payment.inv'

    date_invoice = fields.Date(
        string='Invoice date',
    )

    @api.multi
    def create_invoices(self):
        date = self.date_invoice if self.date_invoice else fields.Date.today()
        self = self.with_context(date_invoice=date)
        return super().create_invoices()
