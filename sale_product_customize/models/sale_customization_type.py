###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models, fields


class SaleCustomizationType(models.Model):
    _name = 'sale.customization.type'
    _description = 'Sale customization type'
    _order = 'name'

    name = fields.Char(
        string='Type',
        translate=True,
        required=True)
