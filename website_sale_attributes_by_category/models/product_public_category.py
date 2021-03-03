###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from openerp import fields, models


class ProductPublicCategory(models.Model):
    _inherit = 'product.public.category'

    attribute_ids = fields.Many2many(
        comodel_name='product.attribute',
        relation='public_category_attribute_rel',
        column1='category_id',
        column2='attribute_id',
        string='Attributes')
