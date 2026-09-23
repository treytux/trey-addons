###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models
from odoo.exceptions import ValidationError


class AccountMove(models.Model):
    _inherit = 'account.move'

    allowed_partner_bank_ids = fields.Many2many(
        comodel_name='res.partner.bank',
        compute='_compute_allowed_partner_bank_ids',
        string='Allowed partner bank accounts',
        readonly=True,
    )

    @api.depends('team_id')
    def _compute_allowed_partner_bank_ids(self):
        Bank = self.env['res.partner.bank']
        for move in self:
            if move.team_id:
                move.allowed_partner_bank_ids = move.team_id.bank_account_ids
            else:
                move.allowed_partner_bank_ids = Bank

    @api.onchange('team_id')
    def _onchange_team_id_partner_bank_domain(self):
        res = {}
        for move in self:
            allowed = move.team_id.bank_account_ids if move.team_id else []
            allowed_ids = allowed.ids if allowed else []
            if (
                move.partner_bank_id and move.partner_bank_id.id
                    not in allowed_ids):
                move.partner_bank_id = False
            if not move.partner_bank_id and len(allowed_ids) >= 1:
                move.partner_bank_id = allowed[0]
            domain = [('id', 'in', allowed_ids)] if allowed_ids else [
                ('id', '=', False),
            ]
            res = {'domain': {'partner_bank_id': domain}}
        return res

    @api.constrains('team_id', 'partner_bank_id', 'move_type')
    def _check_partner_bank_is_allowed(self):
        for move in self:
            if move.move_type not in ('out_invoice', 'out_refund'):
                continue
            if not move.team_id or not move.partner_bank_id:
                continue
            if move.partner_bank_id not in move.allowed_partner_bank_ids:
                raise ValidationError(
                    'Selected bank account is not allowed for the chosen '
                    'sales team.'
                )
