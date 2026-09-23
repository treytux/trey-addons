###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class ProductSuppliernfo(models.Model):
    _inherit = 'product.supplierinfo'

    note = fields.Text(
        string='Note',
    )
