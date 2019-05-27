###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class ProductProduct(models.Model):
    _inherit = 'product.product'

    alert_ids = fields.One2many(
        comodel_name='product.stock.alert',
        inverse_name='product_id',
        string='Stock Alerts')
