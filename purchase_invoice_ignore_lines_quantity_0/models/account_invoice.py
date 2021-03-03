###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, models


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    @api.onchange('purchase_id')
    def purchase_order_change(self):
        super().purchase_order_change()
        if self.invoice_line_ids:
            self.invoice_line_ids = self.invoice_line_ids.filtered(
                lambda ln: ln.quantity != 0)
