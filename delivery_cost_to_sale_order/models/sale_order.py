###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    delivery_cost_to_sale_order = fields.Boolean(
        string='Delivery Cost from Picking',
    )
