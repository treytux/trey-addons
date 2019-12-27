###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class ProductBusinessUnit(models.Model):
    _name = 'product.business.unit'
    _description = 'Product Business Unit'

    name = fields.Char(
        string='Name',
        required=True,
    )
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
        default=lambda self: self.env.user.company_id.id,
    )
    user_id = fields.Many2one(
        comodel_name='res.users',
        string='User',
    )
    area_ids = fields.One2many(
        comodel_name='product.business.area',
        inverse_name='unit_id',
        string='Areas'
    )
