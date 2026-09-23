###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, models


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    @api.model
    def create(self, vals):
        if 'date_invoice' not in self._context:
            return super().create(vals)
        vals['date_invoice'] = self._context['date_invoice']
        return super().create(vals)
