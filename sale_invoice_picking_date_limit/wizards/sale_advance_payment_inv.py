###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class SaleAdvancePaymentInv(models.TransientModel):
    _inherit = 'sale.advance.payment.inv'

    transfered_date = fields.Date(
        string='Transfered date limit',
        help='Invoice quantities transfered to this date',
    )

    @api.multi
    def create_invoices(self):
        self = self.with_context(transfered_date=self.transfered_date)
        res = super(SaleAdvancePaymentInv, self).create_invoices()
        return res
