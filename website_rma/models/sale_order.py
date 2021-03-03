###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    parent_sale_order = fields.Many2one(
        comodel_name='sale.order',
        string='Parent Sale Order',
    )
