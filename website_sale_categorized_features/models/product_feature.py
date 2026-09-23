###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class ProductFeature(models.Model):
    _name = 'product.feature'
    _description = 'Product Features'
    _order = 'sequence'

    def get_name(self):
        return self.public_name if self.public_name else self.name

    sequence = fields.Integer(
        string='Sequence',
        help='Determine the display order',
    )
    name = fields.Char(
        string='Name',
        translate=True,
        required=True,
    )
    value_ids = fields.One2many(
        comodel_name='product.feature.value',
        inverse_name='feature_id',
        string='Features',
        copy=True,
    )
    description = fields.Char(
        string='Description',
    )
    public_name = fields.Char(
        string='Public Name',
    )
