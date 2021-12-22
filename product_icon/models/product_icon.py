###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models, tools


class ProductIcon(models.Model):
    _name = 'product.icon'
    _description = 'Product icon'

    name = fields.Char(
        string='Name',
        required=True,
    )
    image = fields.Binary(
        string='Image',
        attachment=True,
        required=True,
    )
    image_medium = fields.Binary(
        string='Medium-sized image',
        attachment=True,
    )
    image_small = fields.Binary(
        string='Small-sized image',
        attachment=True,
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            tools.image_resize_images(vals)
        return super().create(vals_list)
