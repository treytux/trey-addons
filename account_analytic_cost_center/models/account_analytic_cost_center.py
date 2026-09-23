###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class AccountAnalyticCostCenter(models.Model):
    _name = 'account.analytic.cost_center'
    _description = 'Account analytic cost center'

    name = fields.Char(
        string='Name',
    )
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
        required=True,
        readonly=True,
        default=lambda self: self.env.company.id,
    )
