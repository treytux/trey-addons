###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, api, fields, models
from odoo.exceptions import UserError


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
    cash_count_type = fields.Selection(
        related='team_id.cash_count_type',
        string='Cash count type',
    )
    open_date = fields.Datetime(
        string='Open date',
        default=fields.Datetime.now,
    )
    close_date = fields.Datetime(
        string='Close date',
        track_visibility='onchange',
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
        track_visibility='onchange',
    )
    company_currency = fields.Many2one(
        string='Currency',
        related='company_id.currency_id',
        readonly=True,
        relation='res.currency',
    )
    balance_start = fields.Monetary(
        string='Opening Balance',
        currency_field='company_currency',
        copy=False,
        track_visibility='onchange',
    )
    amount_diff = fields.Monetary(
        string='Difference',
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
        compute='_compute_balance',
    )
    amount_next_session = fields.Monetary(
        string='Amount next session',
        currency_field='company_currency',
        compute='_compute_balance',
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
        string='Mismatch',
        compute='_compute_balance',
        currency_field='company_currency',
    )
    _sql_constraints = [
        ('uniq_name', 'unique(name)',
         'The name of this Sale Session must be unique!'),
    ]

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
        if 'balance_start' not in res and 'team_id' in res:
            sessions = self.search(
                [('team_id', '=', res['team_id'])],
                order='close_date desc, id desc', limit=1)
            res['balance_start'] = sessions.balance_end if sessions else 0
        return res

    @api.depends('open_cash_count_ids', 'close_cash_count_ids')
    def _compute_cash_count_total(self):
        for session in self:
            session.open_cash_count_total = sum(
                session.open_cash_count_ids.mapped('amount_subtotal'))
            session.close_cash_count_total = sum(
                session.close_cash_count_ids.mapped('amount_subtotal'))

    @api.depends('sale_ids', 'sale_ids.state', 'payment_ids',
                 'open_cash_count_ids', 'close_cash_count_ids')
    def _compute_balance(self):
        for session in self:
            sales = session.sale_ids.filtered(
                lambda s: s.state in ['done', 'sale'])
            payments = session.payment_ids.filtered(
                lambda p: not p.invoice_ids)
            session.balance_end = (
                session.balance_start
                + sum(sales.mapped('amount_total'))
                + sum(payments.mapped('amount'))
            )
            session.amount_diff = session.balance_end - session.balance_start
            session.sale_count = len(session.sale_ids)
            session.payment_count = len(session.payment_ids)
            session.close_cash_count_mismatch = (
                session.close_cash_count_total - session.balance_end)
            if session.team_id.cash_money_balance_start:
                amount = (
                    session.balance_end
                    - session.team_id.cash_money_balance_start)
                if amount > 0:
                    session.amount_send = amount
            session.amount_next_session = (
                session.balance_end - session.amount_send)

    @api.constrains('team_id', 'state')
    def _check_state(self):
        for session in self.filtered(lambda s: s.state in ('open', 'draft')):
            results = session.search([
                ('id', '!=', session.id),
                ('team_id', '=', session.team_id.id),
                ('state', 'in', ('open', 'draft')),
            ])
            if results:
                raise UserError(_(
                    'Already exists a sale session for the team "%s". Please '
                    'close the session %s before to create another one for '
                    'the same sale team.') % (
                        session.team_id.name, results.mapped('name')))

    @api.model
    def get_current_sale_session(self, team_id):
        return self.search([
            ('team_id', '=', team_id),
            ('state', '=', 'open'),
        ], limit=1)

    def action_open(self):
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
        self.state = 'validate'
        self.validation_date = fields.Datetime.now()

    def action_revert_to_close(self):
        self.ensure_one()
        self.state = 'close'

    def action_print_close(self):
        report = self.env.ref('sale_session.report_sale_session_ticket_create')
        return report.report_action(self)

    def action_view_close_cash_count(self):
        self.ensure_one()
        if self.close_cash_count_ids:
            raise UserError(_('Cash already closed'))
        wizard = self.env['sale.session.wizard_cash_count'].create({
            'session_id': self.id,
            'journal_id': self.team_id.default_payment_journal_id.id,
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
        action = self.env.ref('account.action_account_payments').read()[0]
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

    def register_payment(self, partner, journal, amount):
        self.ensure_one()
        payment = self.env['account.payment'].create({
            'payment_method_id': self.env.ref(
                'account.account_payment_method_manual_in').id,
            'payment_type': 'inbound',
            'partner_type': 'customer',
            'partner_id': partner.id,
            'journal_id': journal.id,
            'sale_session_id': self.id,
            'amount': amount,
        })
        payment.post()
        return payment
