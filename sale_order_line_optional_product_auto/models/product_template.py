###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    optional_product_method = fields.Selection(
        selection=[
            ('configure', 'When configure product'),
            ('auto', 'When add line in quotation'),
        ],
        string='Optional method',
        default='configure',
    )
