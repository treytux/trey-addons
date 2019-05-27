##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from odoo import api, fields, models, _


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    product_colors_ids = fields.Many2many(
        string=_('Product Colors'),
        comodel_name='product.attribute.value',
        compute='_compute_product_colors_ids')

    @api.multi
    @api.depends('attribute_line_ids.value_ids')
    def _compute_product_colors_ids(self):
        for product in self:
            product_colors_ids = []
            for attribute_line in product.attribute_line_ids:
                for value in attribute_line.value_ids:
                    if value.attribute_id.type == 'color':
                        product_colors_ids.append(value.id)
            product.product_colors_ids = [(6, 0, product_colors_ids)]
