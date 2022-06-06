###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    product_tmpl_code = fields.Char(
        string='Template code',
        help=(
            'It is mandatory if you want to update template data or variants'
            'through import template module.'
        ),
    )
    _sql_constraints = [
        ('uniq_product_tmpl_code', 'unique(product_tmpl_code)',
         'The template code must be unique!'),
    ]
