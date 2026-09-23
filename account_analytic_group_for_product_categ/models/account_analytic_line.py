###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class AccountAnalyticLine(models.Model):
    _inherit = 'account.analytic.line'

    group_analytic_id = fields.Many2one(
        related='product_id.categ_id.group_analytic_id',
        comodel_name='account.analytic.group',
        string='Analytic group',
        store=True,
    )
