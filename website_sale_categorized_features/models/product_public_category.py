###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class ProductPublicCategory(models.Model):
    _inherit = 'product.public.category'

    feature_ids = fields.Many2many(
        comodel_name='product.feature',
        relation='product_category_feature_value_rel',
        column1='category_id',
        column2='feature_id',
        string='Features',
        readonly=False,
    )
