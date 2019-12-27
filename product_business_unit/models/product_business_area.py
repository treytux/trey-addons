###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class ProductBusinessArea(models.Model):
    _name = 'product.business.area'
    _description = 'Product Business Area'

    name = fields.Char(
        string='Name',
        required=True,
    )
    company_id = fields.Many2one(
        comodel_name='res.company',
        related='unit_id.company_id',
        string='Company',
    )
    unit_id = fields.Many2one(
        comodel_name='product.business.unit',
        required=True,
        string='Unit Id',
    )
    user_id = fields.Many2one(
        comodel_name='res.users',
        string='User',
    )
