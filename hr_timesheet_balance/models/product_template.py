###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    analytic_reset_balance = fields.Boolean(
        string='Analytic reset balance',
        help='Reset analytic account balance when an invoice is created with '
             'this product',
    )
