###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class AccountAnalyticLine(models.Model):
    _inherit = 'account.analytic.line'

    plan_analytic_id = fields.Many2one(
        related='product_id.categ_id.plan_analytic_id',
        comodel_name='account.analytic.plan',
        string='Product category analytic plan',
        store=True,
    )
