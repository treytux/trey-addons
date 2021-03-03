###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class CrmTeam(models.Model):
    _inherit = 'crm.team'

    default_payment_journal_id = fields.Many2one(
        comodel_name='account.journal',
        string='Default payment journal',
        domain='[("type", "not in", ["sale", "purchase"])]',
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
        help='Require cash count',
    )
    cash_money_values = fields.Char(
        string='Cash money values',
        help='Add coins and bills monetary values separated by ,',
        default='0.01,0.05,0.10,0.20,0.50,1,2,5,10,20,50,100,200,500',
    )
    cash_money_balance_start = fields.Float(
        string='Balance start min',
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

    def action_open_session(self):
        session = self.env['sale.session'].create({
            'team_id': self.id,
        })
        if self.cash_count_type == 'open-close':
            return session.action_view_open_cash_count()

    def action_close_session(self):
        return self.opened_session_id.action_close()

    def action_register_payment(self):
        action = self.env.ref(
            'sale_session.sale_session_payment_action').read()[0]
        action['context'] = {'default_session_id': self.opened_session_id.id}
        return action
