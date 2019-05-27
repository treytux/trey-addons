###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from openerp import fields, models


class ProductImageTrasient(models.TransientModel):
    _name = 'product.image.transient'

    name = fields.Char(
        string='Name')
    name_slug = fields.Char(
        related='name',
        string='Name')
    image = fields.Binary(
        string='Image')
    product_tmpl_id = fields.Many2one(
        comodel_name='product.template',
        string='Related product')
