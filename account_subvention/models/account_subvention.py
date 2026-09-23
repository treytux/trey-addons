###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class AccountSubvention(models.Model):
    _name = 'account.subvention'
    _description = 'Account subvention'

    name = fields.Char(
        string='Name',
        required=True,
    )
    file_number = fields.Char(
        string='File No',
    )
    description = fields.Char(
        string='Description',
    )
    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Partner',
        required=True,
    )
    account_id = fields.Many2one(
        comodel_name='account.account',
        string='Account',
    )
    journal_id = fields.Many2one(
        comodel_name='account.journal',
        string='Journal',
        required=True,
    )
    account_move_line_ids = fields.One2many(
        comodel_name='account.move.line',
        inverse_name='subvention_id',
        string='Account move lines',
        readonly=True,
    )
    amount = fields.Float(
        string='Subvention amount',
    )
    date_start = fields.Date(
        string='Date start',
    )
    date_end = fields.Date(
        string='Date end',
    )
    date_justification = fields.Date(
        string='Date justification',
    )
    total_subventioned = fields.Float(
        string='Total amount subventioned',
        compute='_compute_total_subventioned',
    )

    total_move_line_ids = fields.Integer(
        string='Total move lines',
        compute='_compute_total_move_line_ids',
    )

    @api.depends('account_move_line_ids')
    def _compute_total_subventioned(self):
        for subvention in self:
            subvention.total_subventioned = sum(
                [aml.debit - aml.credit for aml in
                 subvention.account_move_line_ids])

    def _compute_total_move_line_ids(self):
        for subvention in self:
            subvention.total_move_line_ids = len(subvention.account_move_line_ids)

    def open_lines(self):
        self.ensure_one()
        action = self.env.ref(
            'account_subvention.account_move_lines_action_subvention').read()[0]
        action['domain'] = [('subvention_id', '=', self.id)]
        return action
