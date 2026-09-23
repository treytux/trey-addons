###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, models


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    @api.multi
    def unlink(self):
        for invoice in self:
            settlements = self.env['sale.commission.settlement'].search([
                ('invoice', '=', invoice.id),
            ])
            settlements.write({
                'state': 'settled',
            })
        return super().unlink()

    @api.multi
    def action_invoice_draft(self):
        res = super().action_invoice_draft()
        for invoice in self:
            settlements = self.env['sale.commission.settlement'].search([
                ('invoice', '=', invoice.id),
            ])
            settlements.write({
                'state': 'invoiced',
            })
        return res
