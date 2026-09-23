###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, models


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    @api.multi
    def action_move_create(self):
        for invoice in self:
            if invoice.move_name:
                invoice.invoice_number = invoice.move_name
        return super().action_move_create()
