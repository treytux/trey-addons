###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError


class SaleSession(models.Model):
    _name = 'sale.session'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Sale Session'
    _order = 'id desc'

    name = fields.Char(
        string='Session',
        required=True,
        readonly=True,
        copy=False,
    )
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
        required=True,
        ondelete='set null',
        readonly=True,
        states={'draft': [('readonly', False)]},
    )
    team_id = fields.Many2one(
        comodel_name='crm.team',
        string='Team',
        required=True,
        track_visibility='onchange',
        readonly=True,
        states={'draft': [('readonly', False)]},
    )
    previous_id = fields.Many2one(
        comodel_name='sale.session',
        compute='_compute_previuos_id',
        string='Session previous',
        store=True,
    )
    cash_count_type = fields.Selection(
        related='team_id.cash_count_type',
        string='Cash count type',
    )
    open_date = fields.Datetime(
        string='Open date',
        default=fields.Datetime.now,
        copy=False,
    )
    close_date = fields.Datetime(
        string='Close date',
        track_visibility='onchange',
        copy=False,
    )
    validation_date = fields.Datetime(
        string='Validation date',
        track_visibility='onchange',
    )
    state = fields.Selection(
        selection=[
            ('draft', 'Draft'),
            ('open', 'Opened'),
            ('close', 'Closed'),
            ('validate', 'Validate'),
        ],
        string='State',
        required=True,
        default='draft',
        copy=False,
        track_visibility='onchange',
    )
    company_currency = fields.Many2one(
        string='Currency',
        related='company_id.currency_id',
        readonly=True,
        relation='res.currency',
    )
    total_payment_cash = fields.Monetary(
        string='Payment in cash',
        currency_field='company_currency',
        compute='_compute_balance',
    )
    total_cash = fields.Monetary(
        string='Total cash',
        currency_field='company_currency',
        compute='_compute_balance',
    )
    total_payment_bank = fields.Monetary(
        string='Payment in bank',
        currency_field='company_currency',
        compute='_compute_balance',
    )
    total_credit = fields.Monetary(
        string='Credit sales',
        currency_field='company_currency',
        compute='_compute_balance',
    )
    total_payment = fields.Monetary(
        string='Total',
        currency_field='company_currency',
        compute='_compute_balance',
    )
    balance_start = fields.Monetary(
        string='Opening Balance',
        currency_field='company_currency',
        readonly=True,
        copy=False,
        track_visibility='onchange',
    )
    cash_count_start = fields.Monetary(
        currency_field='company_currency',
        readonly=True,
        copy=False,
    )
    balance_diff = fields.Monetary(
        string='Profit',
        compute='_compute_balance',
        currency_field='company_currency',
    )
    balance_end = fields.Monetary(
        string='Balance end',
        compute='_compute_balance',
        currency_field='company_currency',
    )
    amount_send = fields.Monetary(
        string='Amount to send',
        currency_field='company_currency',
        readonly=True,
    )
    sale_ids = fields.One2many(
        comodel_name='sale.order',
        inverse_name='session_id',
        string='Sales',
    )
    sale_count = fields.Integer(
        string='Sale count',
        compute='_compute_balance',
    )
    payment_ids = fields.One2many(
        comodel_name='account.payment',
        inverse_name='sale_session_id',
        string='Payments',
    )
    payment_count = fields.Integer(
        string='Payment count',
        compute='_compute_balance',
    )
    open_cash_count_ids = fields.One2many(
        comodel_name='sale.session.cash_count',
        inverse_name='session_id',
        string='Open cash count',
        domain=[('type', '=', 'open')],
    )
    open_cash_count_total = fields.Monetary(
        string='Total open',
        compute='_compute_cash_count_total',
        currency_field='company_currency',
    )
    open_cash_count_mismatch = fields.Monetary(
        string='Open mismatch',
        compute='_compute_balance',
        currency_field='company_currency',
    )
    close_cash_count_ids = fields.One2many(
        comodel_name='sale.session.cash_count',
        inverse_name='session_id',
        string='Close cash count',
        domain=[('type', '=', 'close')],
    )
    close_cash_count_total = fields.Monetary(
        string='Total close',
        compute='_compute_cash_count_total',
        currency_field='company_currency',
    )
    close_cash_count_mismatch = fields.Monetary(
        string='Close mismatch',
        compute='_compute_balance',
        currency_field='company_currency',
    )
    validate_move_id = fields.Many2one(
        comodel_name='account.move',
        string='Validation',
    )
    mismatch_open_move_ids = fields.Many2many(
        comodel_name='account.move',
        relation='sale_session_mismatch_open_account_move_rel',
        column1='sale_session_id',
        column2='account_move_id',
        string='Mismatch open',
    )
    mismatch_close_move_ids = fields.Many2many(
        comodel_name='account.move',
        relation='sale_session_mismatch_close_account_move_rel',
        column1='sale_session_id',
        column2='account_move_id',
        string='Mismatch close',
    )
    validate_journal_id = fields.Many2one(
        comodel_name='account.journal',
        string='Validation journal',
    )
    _sql_constraints = [
        ('uniq_name', 'unique(name)',
         'The name of this Sale Session must be unique!'),
    ]

    @api.constrains('previous_id')
    def _check_previous_id(self):
        for session in self:
            if not session.previous_id:
                continue
            if not session.previous_id.previous_id:
                continue
            if session != session.previous_id.previous_id:
                continue
            raise ValidationError(_(
                'Previous cross-reference.\n'
                'Session linked to a previous session already linked to '
                'this session'))

    @api.model
    def default_get(self, fields):
        res = super().default_get(fields)
        if 'company_id' not in res:
            res['company_id'] = self.env.user.company_id.id
        if 'name' not in res:
            res['name'] = self.env['ir.sequence'].with_context(
                company_id=res['company_id']).next_by_code('sale.session')
        return res

    @api.model
    def _add_missing_default_values(self, values):
        res = super()._add_missing_default_values(values)
        if 'team_id' not in res or 'balance_start' in res:
            return res
        crm_team = self.env['crm.team'].browse(res['team_id'])
        res['balance_start'] = crm_team.get_actual_total_cash()
        return res

    @api.depends('state', 'team_id')
    def _compute_previuos_id(self):
        for session in self:
            id = isinstance(session.id, models.NewId) and -1 or session.id
            previous = self.search([
                ('id', '!=', id),
                ('team_id', '=', session.team_id.id),
                ('state', 'in', ['open', 'close', 'validate']),
            ], order='id desc', limit=1)
            if not previous:
                continue
            if session.state in ('draft', 'open'):
                session.previous_id = previous.id
            if previous and session.state == 'draft':
                session.balance_start = session.team_id.get_actual_total_cash()

    @api.depends('open_cash_count_ids', 'close_cash_count_ids')
    def _compute_cash_count_total(self):
        for session in self:
            session.open_cash_count_total = sum(
                session.open_cash_count_ids.mapped(
                    'cash_count_line_ids.amount_subtotal'))
            session.close_cash_count_total = sum(
                session.close_cash_count_ids.mapped(
                    'cash_count_line_ids.amount_subtotal'))

    @api.depends('sale_ids', 'sale_ids.state', 'payment_ids', 'balance_start',
                 'open_cash_count_ids', 'close_cash_count_ids', 'amount_send')
    def _compute_balance(self):
        for session in self.sorted(lambda s: s.id):
            outbound_payments = session.payment_ids.filtered(
                lambda p: p.payment_type == 'outbound' and p.invoice_ids)
            cash_outbound_payments = outbound_payments.filtered(
                lambda p: p.journal_id.type == 'cash')
            bank_outbound_payments = outbound_payments.filtered(
                lambda p: p.journal_id.type == 'bank')
            inbound_payments = session.payment_ids.filtered(
                lambda p: p.payment_type == 'inbound')
            cash_inbound_payments = inbound_payments.filtered(
                lambda p: p.journal_id.type == 'cash')
            bank_inbound_payments = inbound_payments.filtered(
                lambda p: p.journal_id.type == 'bank')
            session.total_payment_cash = (
                sum(cash_inbound_payments.mapped('amount'))
                - sum(cash_outbound_payments.mapped('amount')))
            session.total_payment_bank = (
                sum(bank_inbound_payments.mapped('amount'))
                - sum(bank_outbound_payments.mapped('amount')))
            session.total_payment = (
                session.total_payment_cash + session.total_payment_bank
            )
            session.balance_end = (
                session.balance_start
                + sum(inbound_payments.mapped('amount'))
                - sum(outbound_payments.mapped('amount'))
            )
            session.total_cash = (
                session.total_payment_cash + session.balance_start)
            session.total_credit = session.balance_end - session.total_payment
            session.balance_diff = session.balance_end - session.balance_start
            session.sale_count = len(session.sale_ids)
            session.payment_count = len(session.payment_ids)
            session.open_cash_count_mismatch = (
                (session.open_cash_count_total - session.balance_start)
                if session.open_cash_count_total
                else 0)
            session.close_cash_count_mismatch = (
                (session.total_cash - session.close_cash_count_total)
                if session.close_cash_count_ids
                else 0)

    @api.constrains('team_id', 'state')
    def _check_state(self):
        for session in self.filtered(lambda s: s.state == 'open'):
            results = session.search([
                ('id', '!=', session.id),
                ('team_id', '=', session.team_id.id),
                ('state', '=', 'open'),
            ])
            if results:
                raise ValidationError(_(
                    'Already exists a sale session for the team "%s". Please '
                    'close the session %s before to create another one for '
                    'the same sale team.') % (
                        session.team_id.name,
                        ', '.join(results.mapped('name'))))

    @api.model
    def get_current_sale_session(self, team_id):
        return self.search([
            ('team_id', '=', team_id),
            ('state', '=', 'open'),
        ], limit=1)

    def action_open(self):
        self.ensure_one()
        if not self.team_id.cash_payment_journal_id:
            raise UserError(
                _('The session for team %s need a cash payment journal.') % (
                    self.team_id.name))
        if self.team_id.cash_min_for_open_session > self.balance_start:
            raise UserError(_(
                'To open the session you must do so with more than %s in '
                'cash.') % self.team_id.cash_min_for_open_session)
        date = self.open_date and self.open_date.date() or fields.Date.today()
        self.balance_start = self.team_id.with_context(
            date=date).get_actual_total_cash()
        if self.team_id.cash_count_type == 'open-close':
            return self.action_view_open_cash_count()
        self.state = 'open'

    def action_close(self):
        self.ensure_one()
        if self.cash_count_type != 'none' and not self.close_cash_count_ids:
            return self.action_view_close_cash_count()
        wizard = self.env['sale.session.close'].create({
            'session_id': self.id,
        })
        action = self.env.ref(
            'sale_session.sale_session_close_action').read()[0]
        action['res_id'] = wizard.id
        return action

    def action_validate(self):
        self.ensure_one()
        wizard = self.env['sale.session.validate'].create({
            'session_id': self.id,
            'amount_send': self.amount_send,
        })
        action = self.env.ref(
            'sale_session.sale_session_validate_action').read()[0]
        action['res_id'] = wizard.id
        return action

    def action_revert_to_open(self):
        self.ensure_one()
        if self.mismatch_close_move_ids:
            if all(mv.state == 'posted' for mv in self.mismatch_close_move_ids):
                self.mismatch_close_move_ids.button_cancel()
            self.mismatch_close_move_ids.unlink()
        self.write({
            'state': 'open',
            'close_date': False,
            'amount_send': 0,
        })

    def action_revert_to_close(self):
        self.ensure_one()
        if self.validate_move_id:
            if self.validate_move_id.state == 'posted':
                self.validate_move_id.button_cancel()
            self.validate_move_id.unlink()
        self.write({
            'state': 'close',
            'validation_date': False,
        })

    def action_unlink_close_cash_counts(self):
        self.close_cash_count_ids.unlink()

    def action_print_close(self):
        report = self.env.ref('sale_session.report_sale_session_ticket_create')
        return report.report_action(self)

    def action_view_close_cash_count(self):
        self.ensure_one()
        if self.close_cash_count_ids:
            raise UserError(_('Cash already closed'))
        wizard = self.env['sale.session.wizard_cash_count'].create({
            'session_id': self.id,
            'type': 'close',
        })
        return wizard.action_get()

    def action_view_open_cash_count(self):
        self.ensure_one()
        if self.open_cash_count_ids:
            raise UserError(_('Cash already opened'))
        wizard = self.env['sale.session.wizard_cash_count'].create({
            'session_id': self.id,
            'type': 'open',
        })
        return wizard.action_get()

    def action_view_payments(self):
        action = self.env.ref(
            'sale_session.action_account_payment_sale_session').read()[0]
        action['domain'] = [('id', 'in', self.payment_ids.ids)]
        action['context'] = {
            'search_default_session_id': self[0].id,
        }
        return action

    def action_view_sales(self):
        action = self.env.ref(
            'sale.action_quotations_with_onboarding').read()[0]
        action['domain'] = [('id', 'in', self.sale_ids.ids)]
        action['context'] = {
            'pivot_measures': ['product_qty'],
            'search_default_team_id': self[0].team_id.id,
        }
        return action

    def register_payment(
            self, partner, journal, amount, payment_type='inbound',
            communication=''):
        self.ensure_one()
        payment_method_id = (
            payment_type == 'inbound'
            and self.env.ref('account.account_payment_method_manual_in').id
            or self.env.ref('account.account_payment_method_manual_out').id
        )
        partner_type = payment_type == 'inbound' and 'customer' or 'supplier'
        payment = self.env['account.payment'].create({
            'payment_method_id': payment_method_id,
            'payment_type': payment_type,
            'partner_type': partner_type,
            'partner_id': partner and partner.id or False,
            'journal_id': journal.id,
            'sale_session_id': self.id,
            'amount': amount,
            'communication': communication,
        })
        payment.post()
        return payment
