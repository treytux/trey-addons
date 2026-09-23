###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    qty_available_not_res = fields.Float(
        related='product_id.qty_available_not_res',
    )
