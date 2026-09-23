###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class ProductCategory(models.Model):
    _inherit = 'product.category'

    group_analytic_id = fields.Many2one(
        comodel_name='account.analytic.group',
        string='Analytic group',
    )
