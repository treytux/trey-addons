###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    product_unit_id = fields.Many2one(
        comodel_name='product.business.unit',
        related='product_id.unit_id',
        string='Business unit',
        readonly=True,
    )
