###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models


class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'

    def _prepare_agents_vals_partner(self, partner):
        apply_partner_group = (
            self._name == 'account.invoice.line'
            and self.sale_line_ids.mapped('order_id')
            and self.sale_line_ids.mapped('order_id')[0].partner_group_id
            and self.sale_line_ids.mapped('order_id')[0].partner_invoice_id
            != self.sale_line_ids.mapped('order_id')[0].partner_id
        )
        if apply_partner_group:
            partner = self.sale_line_ids.mapped('order_id.partner_id')[0]
        return super()._prepare_agents_vals_partner(partner=partner)
