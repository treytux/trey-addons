###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import odoo.addons.decimal_precision as dp
from odoo import fields, models


class ProductCustomerInfo(models.Model):
    _inherit = 'product.customerinfo'

    margin_limit = fields.Float(
        string='Margin limit (%)',
        digits=dp.get_precision('Discount'),
    )
