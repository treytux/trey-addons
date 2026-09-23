###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class AccountAnalyticLine(models.Model):
    _inherit = 'account.analytic.line'

    group_id = fields.Many2one(
        comodel_name='account.analytic.group',
        string='Analytic Group',
        index=True,
    )
