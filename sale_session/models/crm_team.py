###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class CrmTeam(models.Model):
    _inherit = 'crm.team'

    cash_payment_journal_id = fields.Many2one(
        comodel_name='account.journal',
        string='Cash payment journal',
        domain='[("type", "=", "cash")]',
    )
    require_sale_session = fields.Boolean(
        string='Require sale session',
    )
    cash_count_type = fields.Selection(
        selection=[
            ('none', 'Not need cash count'),
            ('close', 'Required only when close a session'),
            ('open-close', 'Required when open and close a session'),
        ],
        string='Cash count',
        default='none',
    )
    require_cash_count = fields.Boolean(
        string='Require cash count',
    )
    allow_edit_amount_send = fields.Boolean(
        string='Allow edit amount to send',
        help='Allow to edit amount to send on validate session',
    )
    force_stock = fields.Boolean(
        string='Force stock availability',
        help='Force stock availability in stock pickings',
    )
    cash_money_values = fields.Char(
        string='Cash money values',
        help='Add coins and bills monetary values separated by ,',
        default='0.01,0.05,0.10,0.20,0.50,1,2,5,10,20,50,100,200,500',
    )
    cash_min_for_open_session = fields.Float(
        string='Min cash for open session',
    )
    mismatch_account = fields.Many2one(
        comodel_name='account.account',
        string='Mismatch account',
    )
    session_ids = fields.One2many(
        comodel_name='sale.session',
        inverse_name='team_id',
        string='Sessions',
    )
    session_count = fields.Integer(
        string='Session count',
        compute='_compute_session_count',
    )
    opened_session_id = fields.Many2one(
        comodel_name='sale.session',
        compute='_compute_opened_session',
        string='Session opened',
    )
    default_partner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Default partner',
    )
    simplified_journal_id = fields.Many2one(
        comodel_name='account.journal',
        string='Simplified journal',
        domain='[("type", "=", "sale")]',
    )
    autocomplete_amount = fields.Boolean(
        string='Autocomplete amount',
        help='Autocomplete amount paid',
    )

    @api.depends('session_ids')
    def _compute_opened_session(self):
        for team in self:
            team.opened_session_id = team.session_ids.filtered(
                lambda s: s.state == 'open')

    @api.depends('session_ids')
    def _compute_session_count(self):
        for team in self:
            team.session_count = len(team.session_ids)

    def get_cash_money_values(self):
        self.ensure_one()
        if not self.cash_money_values:
            return []
        return sorted(
            [float(v) for v in self.cash_money_values.split(',') if v])

    @api.constrains('cash_money_values')
    def _check_cash_money_values(self):
        for team in self:
            if not team.cash_money_values:
                continue
            try:
                team.get_cash_money_values()
            except Exception:
                raise ValidationError(_(
                    'Cash money values field must monetary values separated '
                    'by ,'))

    def get_actual_total_cash(self, journal_id=False):
        cash_journals = self.payment_journal_ids.filtered(
            lambda j: j.type == 'cash')
        if journal_id:
            cash_journals = cash_journals.filtered(
                lambda j: j.id == journal_id.id)
        move_line_obj = self.env['account.move.line']
        total = 0
        date = self._context.get('date', fields.Date.today())
        for account in cash_journals.mapped('default_credit_account_id'):
            moves = move_line_obj.read_group(
                [
                    ('account_id', '=', account.id),
                    ('move_id.state', '=', 'posted'),
                    ('date', '<=', date),
                ],
                ['debit', 'credit'], ['account_id'])
            total += sum([m['debit'] - m['credit'] for m in moves])
        return total

    def action_open_session(self):
        session = self.env['sale.session'].create({
            'team_id': self.id,
        })
        if self.cash_count_type == 'open-close':
            return session.action_view_open_cash_count()
        session.action_open()

    def action_close_session(self):
        return self.opened_session_id.action_close()

    def action_register_payment(self):
        action = self.env.ref(
            'sale_session.sale_session_payment_action').read()[0]
        action['context'] = {'default_session_id': self.opened_session_id.id}
        return action
