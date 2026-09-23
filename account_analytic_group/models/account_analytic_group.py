###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class AccountAnalyticGroup(models.Model):
    _name = 'account.analytic.group'
    _description = 'Analytic Group'
    _order = 'name'

    name = fields.Char(
        string='Name',
        required=True,
        translate=True,
    )
    color = fields.Integer(
        string='Color Index',
    )
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
        default=lambda self: self.env.company,
    )
