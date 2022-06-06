###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models


class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'

    def _prepare_agents_vals(self, vals=None):
        res = super()._prepare_agents_vals(vals=vals)
        invoice = (
            self and self.invoice_id
            or self.env['account.invoice'].browse(vals['invoice_id']))
        if not invoice or invoice.type.startswith('out_'):
            return res
        return self._prepare_agents_vals_partner(invoice.partner_id)
