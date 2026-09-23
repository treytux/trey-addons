###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    carrier_ids = fields.Many2many(
        comodel_name='delivery.carrier',
        relation='product_template_delivery_carrier_rel',
        column1='product_template_id',
        column2='carrier_id',
        string='Delivery Carriers',
    )
