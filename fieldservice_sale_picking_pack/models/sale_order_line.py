###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    sale_line_fsm_id = fields.Many2one(
        comodel_name='sale.order.line',
        string='Related with',
        readonly=True,
        help='Product line installation with which it is related. It is used '
             'so that this product is added to the fsm order of the related '
             'product when the sales order is confirmed.\nUse the "Relate to '
             'installations" wizard to map them if you need to.'
    )
