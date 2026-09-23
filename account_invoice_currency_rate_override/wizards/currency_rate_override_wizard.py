###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, api, fields, models
from odoo.exceptions import UserError


class CurrencyRateOverrideWizard(models.TransientModel):
    _name = 'currency.rate.override.wizard'
    _description = 'Currency Rate Override Wizard'

    move_id = fields.Many2one(
        comodel_name='account.move',
        string='Invoice',
        readonly=True,
        required=True,
    )
    currency_id = fields.Many2one(
        comodel_name='res.currency',
        string='Foreign Currency',
        readonly=True,
        related='move_id.currency_id',
    )
    company_currency_id = fields.Many2one(
        comodel_name='res.currency',
        string='Company Currency',
        readonly=True,
        related='move_id.company_currency_id',
    )
    amount_currency_total = fields.Float(
        string='Amount in Foreign Currency',
        readonly=True,
        digits='Account',
    )
    amount_company_total = fields.Float(
        string='Current Amount in Company Currency',
        readonly=True,
        digits='Account',
    )
    current_rate = fields.Float(
        string='Current Rate',
        readonly=True,
        digits=(16, 6),
    )
    new_amount_company = fields.Float(
        string='New Amount in Company Currency',
        required=True,
        digits='Account',
    )
    new_rate = fields.Float(
        string='New Rate',
        readonly=True,
        digits=(16, 6),
    )

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        move_id = self.env.context.get('default_move_id')
        if not move_id:
            return res
        move = self.env['account.move'].browse(move_id)
        fc_total = move._get_foreign_currency_total()
        cc_total = move._get_company_currency_total()
        res.update({
            'amount_currency_total': fc_total,
            'amount_company_total': cc_total,
            'current_rate': cc_total / fc_total if fc_total else 1.0,
            'new_amount_company': cc_total,
            'new_rate': cc_total / fc_total if fc_total else 1.0,
        })
        return res

    @api.onchange('new_amount_company')
    def _onchange_new_amount_company(self):
        if self.new_amount_company and self.amount_currency_total:
            self.new_rate = (
                self.new_amount_company / self.amount_currency_total)
        else:
            self.new_rate = 0.0

    def action_apply(self):
        self.ensure_one()
        move = self.move_id
        if move.state != 'posted':
            raise UserError(_('The invoice must be in posted state.'))
        if move.payment_state != 'not_paid':
            raise UserError(
                _('The invoice is already reconciled. '
                  'Cannot adjust the currency rate.')
            )
        if not move.currency_id or move.currency_id == move.company_currency_id:
            raise UserError(
                _('The invoice is not in a foreign currency.')
            )
        fc_total = self.amount_currency_total
        if not fc_total:
            raise UserError(
                _('No foreign currency amount found on the invoice.')
            )
        old_cc_total = self.amount_company_total
        new_cc_total = self.new_amount_company
        if move.company_currency_id.is_zero(new_cc_total):
            raise UserError(
                _('The new company currency amount must be non-zero.')
            )
        if move.currency_id.compare_amounts(
            fc_total / old_cc_total, fc_total / new_cc_total
        ) == 0:
            raise UserError(
                _('The new amount is the same as the current amount. '
                  'Nothing to do.')
            )
        factor = new_cc_total / old_cc_total
        move.button_draft()
        line_cmds = []
        for line in move.line_ids:
            new_balance = line.balance * factor
            new_balance = move.company_currency_id.round(new_balance)
            vals = {
                'balance': new_balance,
                'debit': new_balance if new_balance > 0.0 else 0.0,
                'credit': -new_balance if new_balance < 0.0 else 0.0,
            }
            if line.currency_id and line.currency_id \
                    != move.company_currency_id:
                if line.amount_currency:
                    vals['amount_currency'] = line.amount_currency
            line_cmds.append((1, line.id, vals))
        move.write({'line_ids': line_cmds})
        move.action_post()
        return {'type': 'ir.actions.act_window_close'}
