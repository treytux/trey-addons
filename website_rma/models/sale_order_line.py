###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class SaleOrder(models.Model):
    _inherit = 'sale.order.line'

    qty_return = fields.Float(
        comodel_name='sale.order.line',
        string='Returned Quantity',
    )
