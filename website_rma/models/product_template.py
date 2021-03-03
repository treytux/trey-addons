###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class SaleOrder(models.Model):
    _inherit = 'product.template'

    is_returnable = fields.Boolean(
        default=True,
        string='Is returnable',
    )
