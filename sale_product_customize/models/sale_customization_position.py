###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models, fields


class SaleCustomizationPosition(models.Model):
    _name = 'sale.customization.position'
    _description = 'Sale customization position'
    _order = 'name'

    name = fields.Char(
        string='Position',
        translate=True,
        required=True)
