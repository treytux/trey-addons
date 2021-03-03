###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class SaleCustomizationColor(models.Model):
    _name = 'sale.customization.color'
    _description = 'Sale customization color'
    _order = 'name'

    name = fields.Char(
        string='Color',
        required=True,
    )
