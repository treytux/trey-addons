###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, models


class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'

    @api.onchange('product_id')
    def _onchange_product_id(self):
        super()._onchange_product_id()
        self.discount = sum(
            self.mapped('invoice_id.global_discount_ids.total_percent'))
