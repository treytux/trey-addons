###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class ProductTemplateIcon(models.Model):
    _name = 'product.template.icon'
    _description = 'Product template icon'
    _rec_name = 'icon_id'
    _order = 'sequence, id'

    sequence = fields.Integer(
        string='Sequence',
        default=10,
    )
    icon_id = fields.Many2one(
        comodel_name='product.icon',
        string='Icon',
        index=True,
        required=True,
        ondelete='cascade',
    )
    product_template_id = fields.Many2one(
        comodel_name='product.template',
        string='Product template',
        index=True,
        required=True,
        ondelete='cascade',
    )
    image_128 = fields.Image(
        string='Image',
        related='icon_id.image_128',
    )
