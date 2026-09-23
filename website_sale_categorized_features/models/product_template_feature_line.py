###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class ProductFeatureLine(models.Model):
    _name = 'product.template.feature.line'
    _description = 'Product Template Feature Lines'
    _rec_name = 'feature_id'

    template_id = fields.Many2one(
        comodel_name='product.template',
        string='Product',
        required=True,
        ondelete='cascade',
    )
    feature_id = fields.Many2one(
        comodel_name='product.feature',
        string='Feature',
        required=True,
        ondelete='restrict',
    )
    value_ids = fields.Many2many(
        comodel_name='product.feature.value',
        relation='product_template_feature_line_feature_value_rel',
        column1='line_id',
        column2='value_id',
        string='Values',
    )
