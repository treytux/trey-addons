###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models


class AccountMove(models.Model):
    _inherit = 'account.move'

    def action_currency_rate_override(self):
        self.ensure_one()
        return {
            'name': 'Adjust Currency Rate',
            'type': 'ir.actions.act_window',
            'res_model': 'currency.rate.override.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_move_id': self.id,
            },
        }

    def _get_company_currency_total(self):
        self.ensure_one()
        receivable_lines = self.line_ids.filtered(
            lambda ln: ln.account_id.account_type
            in ('asset_receivable', 'liability_payable')
        )
        return abs(sum(receivable_lines.mapped('balance')))

    def _get_foreign_currency_total(self):
        self.ensure_one()
        receivable_lines = self.line_ids.filtered(
            lambda ln: ln.account_id.account_type
            in ('asset_receivable', 'liability_payable')
        )
        return abs(sum(receivable_lines.mapped('amount_currency')))
