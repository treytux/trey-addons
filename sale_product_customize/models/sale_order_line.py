###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    customization_id = fields.Many2one(
        comodel_name='sale.customization',
        string='Customization')
