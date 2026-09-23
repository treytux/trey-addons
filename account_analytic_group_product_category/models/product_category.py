###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class ProductCategory(models.Model):
    _inherit = 'product.category'

    analytic_group_id = fields.Many2one(
        comodel_name='account.analytic.group',
        string='Analytic Group',
        help='Analytic group assigned from this category. '
             'If not set, parent categories are checked recursively.',
    )
