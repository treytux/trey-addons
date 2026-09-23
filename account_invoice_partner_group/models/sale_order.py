###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.multi
    def action_invoice_create(self, grouped=False, final=False):
        invoice_ids = super().action_invoice_create(
            grouped=grouped, final=final)
        for sale in self:
            for invoice in sale.invoice_ids:
                if sale.partner_group_id:
                    invoice.partner_group_id = sale.partner_group_id
        return invoice_ids
