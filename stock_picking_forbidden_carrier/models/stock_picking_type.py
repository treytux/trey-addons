###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class StockPickingType(models.Model):
    _inherit = 'stock.picking.type'

    forbidden_carriers = fields.Many2many(
        comodel_name='delivery.carrier',
        column1='picking_type_id',
        column2='carrier_id',
        relation='stock_picking_type2delivery_carrier_rel',
        string='Forbidden carriers',
    )
