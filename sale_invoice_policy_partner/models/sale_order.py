###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.onchange('partner_invoice_id')
    def on_change_partner_invoice_id(self):
        if self.partner_id.invoice_policy:
            self.invoice_policy = self.partner_id.invoice_policy
