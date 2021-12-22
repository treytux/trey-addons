###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class ProductSetupProperty(models.Model):
    _name = 'product.setup.property'
    _description = 'Product setup property'

    name = fields.Char(
        string='Name',
    )
    categ_id = fields.Many2one(
        comodel_name='product.setup.category',
        string='Category',
    )
