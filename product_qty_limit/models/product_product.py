##############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
##############################################################################
from odoo import fields, models


class ProductProduct(models.Model):
    _inherit = 'product.product'

    qty_limit = fields.Integer(
        string='Qty Limit',
        help='Maximum quantity allowed in sales. 0 means no limit.',
    )
