###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, api, exceptions, fields, models


class SaleSessionClose(models.TransientModel):
    _name = 'sale.session.close'
    _description = 'Wizard to close a sale session'

    session_id = fields.Many2one(
        comodel_name='sale.session',
        string='Sale Session',
        required=True,
        readonly=True,
    )
    team_id = fields.Many2one(
        related='session_id.team_id',
    )
    company_currency = fields.Many2one(
        related='session_id.company_id.currency_id',
    )
    total_payment_cash = fields.Monetary(
        related='session_id.total_payment_cash',
        currency_field='company_currency',
    )
    total_cash = fields.Monetary(
        related='session_id.total_cash',
        currency_field='company_currency',
    )
    balance_start = fields.Monetary(
        related='session_id.balance_start',
        currency_field='company_currency',
    )
    balance_end = fields.Monetary(
        related='session_id.balance_end',
        currency_field='company_currency',
    )
    close_cash_count_mismatch = fields.Monetary(
        related='session_id.close_cash_count_mismatch',
        currency_field='company_currency',
    )
    close_cash_count_total = fields.Monetary(
        string='Total cash count close',
        related='session_id.close_cash_count_total',
        currency_field='company_currency',
    )
    amount_send = fields.Monetary(
        string='Amount to send',
        currency_field='company_currency',
    )
    amount_next_session = fields.Monetary(
        string='Amount next session',
        currency_field='company_currency',
        compute='_compute_amount_next_session',
    )
    total_payment_cash = fields.Monetary(
        related='session_id.total_payment_cash',
        currency_field='company_currency',
    )
    journal_line_ids = fields.One2many(
        comodel_name='sale.session.close.journal_line',
        inverse_name='close_id',
        string='Journal lines',
        readonly=True,
    )
    allow_amount_send = fields.Boolean(
        readonly=True,
        default=True,
    )

    @api.depends('amount_send', 'total_payment_cash')
    def _compute_amount_next_session(self):
        for wizard in self:
            cash = (
                wizard.session_id.close_cash_count_ids
                and wizard.close_cash_count_total or wizard.total_cash)
            wizard.amount_next_session = cash - wizard.amount_send

    @api.model
    def create(self, vals):
        wizard = super().create(vals)
        group_journals = {}
        for payment in wizard.session_id.payment_ids:
            item = group_journals.setdefault(payment.journal_id, [])
            item.append(payment.amount)
        for journal, amounts in group_journals.items():
            wizard.journal_line_ids.create({
                'close_id': wizard.id,
                'journal_id': journal.id,
                'amount_total': sum(amounts),
            })
        wizard.allow_amount_send = not len(wizard.journal_line_ids.filtered(
            lambda jl: jl.journal_id.type == 'cash')) > 1 or True
        min_cash = wizard.team_id.cash_min_for_open_session
        if min_cash:
            amount = wizard.session_id.total_payment_cash - min_cash
            if amount > 0:
                wizard.amount_send = amount
        return wizard

    def action_confirm(self):
        self.ensure_one()
        session = self.session_id
        total_journal_cash = self.team_id.get_actual_total_cash()
        if self.amount_send > total_journal_cash:
            raise exceptions.ValidationError(_(
                'You can\'t send %s, it has to be a value under cash payments '
                'total %s') % (self.amount_send, total_journal_cash))
        session.write({
            'state': 'close',
            'amount_send': self.amount_send,
            'close_date': fields.Datetime.now(),
        })
        if not session.close_cash_count_mismatch:
            session.action_print_close()
            return
        reference = _('Mismatch when close sale session %s') % session.name
        for close_cash_count in session.close_cash_count_ids:
            journal = close_cash_count.journal_id
            journal_mismatch = (
                session.team_id.get_actual_total_cash(journal)
                - close_cash_count.amount_total)
            if not journal_mismatch:
                continue
            if not journal.default_debit_account_id:
                raise exceptions.UserError(_(
                    'Journal "%s" needs a default debit account') % (
                    journal.name))
            if not self.team_id.mismatch_account:
                raise exceptions.UserError(
                    _('Team "%s" needs a mismatch account') % self.team_id.name)
            debit_vals = {
                'name': reference,
                'partner_id': session.company_id.partner_id.id,
                'debit': abs(journal_mismatch) if journal_mismatch < 0 else 0,
                'credit': abs(journal_mismatch) if journal_mismatch > 0 else 0,
                'account_id': journal.default_debit_account_id.id,
            }
            credit_vals = debit_vals.copy()
            credit_vals.update({
                'debit': debit_vals['credit'],
                'credit': debit_vals['debit'],
                'account_id': self.team_id.mismatch_account.id,
            })
            mismatch_move = self.env['account.move'].create({
                'ref': reference,
                'journal_id': journal.id,
                'line_ids': [(0, 0, debit_vals), (0, 0, credit_vals)],
            })
            session.mismatch_close_move_ids = [(4, mismatch_move.id)]
        session.action_print_close()


class SaleSessionCloseJournalLine(models.TransientModel):
    _name = 'sale.session.close.journal_line'
    _description = 'Journal lines in close wizard'

    close_id = fields.Many2one(
        comodel_name='sale.session.close',
        string='Close wizard',
        required=True,
    )
    journal_id = fields.Many2one(
        comodel_name='account.journal',
        string='Journal',
    )
    amount_total = fields.Float(
        string='Total',
    )
