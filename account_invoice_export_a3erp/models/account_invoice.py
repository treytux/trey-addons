###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    def action_export_invoice_a3erp(self):
        self.ensure_one()
        action = self.env.ref(
            'account_invoice_export_a3erp.account_invoice_export_a3erp_action')
        action = action.read()[0]
        return action
