###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


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
    balance_start = fields.Monetary(
        related='session_id.balance_start',
        currency_field='company_currency',
    )
    amount_diff = fields.Monetary(
        related='session_id.amount_diff',
        currency_field='company_currency',
        string='Transactions',
    )
    balance_end = fields.Monetary(
        related='session_id.balance_end',
        currency_field='company_currency',
    )
    amount_send = fields.Monetary(
        related='session_id.amount_send',
        currency_field='company_currency',
    )
    amount_next_session = fields.Monetary(
        related='session_id.amount_next_session',
        currency_field='company_currency',
    )
    bank_payment = fields.Monetary(
        string='Bank payments',
        currency_field='company_currency',
        compute='_compute_resume',
    )
    cash_payment = fields.Monetary(
        string='Cash payments',
        currency_field='company_currency',
        compute='_compute_resume',
    )
    journal_line_ids = fields.One2many(
        comodel_name='sale.session.close.journal_line',
        inverse_name='close_id',
        string='Journal lines',
        readonly=True,
    )

    @api.depends('session_id', 'journal_line_ids')
    def _compute_resume(self):
        def get_journal_total(wizard, type):
            lines = wizard.journal_line_ids.filtered(
                lambda l: l.journal_id.type == type)
            return lines.mapped('amount_total')

        for wizard in self:
            wizard.bank_payment = sum(get_journal_total(wizard, 'bank'))
            wizard.cash_payment = sum(get_journal_total(wizard, 'cash'))

    @api.model
    def create(self, vals):
        wizard = super().create(vals)
        group_journals = {}
        for payment in wizard.session_id.payment_ids:
            item = group_journals.setdefault(payment.journal_id, [])
            item.append(payment.amount)
        for journal, amounts in group_journals.items():
            self.journal_line_ids.create({
                'close_id': wizard.id,
                'journal_id': journal.id,
                'amount_total': sum(amounts),
            })
        return wizard

    def action_confirm(self):
        self.ensure_one()
        self.session_id.state = 'close'
        self.session_id.close_date = fields.Datetime.now()
        self.session_id.action_print_close()


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
