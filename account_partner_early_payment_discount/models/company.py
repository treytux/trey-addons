###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models, fields


class ResCompany(models.Model):
    _inherit = 'res.company'

    discount_product_id = fields.Many2one(
        comodel_name='product.product',
        string='Early Payment Discount Product',
        required=False,
        domain=[('type', '=', 'service')])
