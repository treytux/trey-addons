###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class AccountAnalyticLine(models.Model):
    _inherit = 'account.analytic.line'

    production_id = fields.Many2one(
        comodel_name='mrp.production',
        string='Manufacturing Order',
        ondelete='set null',
    )
