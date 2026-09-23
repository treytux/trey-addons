###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models
from odoo.exceptions import ValidationError


class CrmTeam(models.Model):
    _inherit = 'crm.team'

    company_partner_id = fields.Many2one(
        comodel_name='res.partner',
        related='company_id.partner_id',
        string='Company partner',
        readonly=True,
    )
    bank_account_ids = fields.Many2many(
        comodel_name='res.partner.bank',
        relation='crm_team_res_partner_bank_rel',
        column1='team_id',
        column2='bank_id',
        string='Recipient Banks',
        help='Bank accounts available to be selected on quotes and invoices '
        'for this sales team.',
    )

    @api.constrains('bank_account_ids', 'company_id')
    def _check_bank_accounts_company_partner(self):
        for team in self:
            company_partner = team.company_id.partner_id
            invalid = team.bank_account_ids.filtered(
                lambda b: b.partner_id != company_partner)
            if invalid:
                raise ValidationError(
                    'Some selected bank accounts do not belong to the '
                    'company partner.')
