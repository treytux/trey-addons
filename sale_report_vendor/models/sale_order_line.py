###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    vendor_id = fields.Many2one(
        comodel_name='res.partner',
        string='Vendor',
    )

    @api.onchange('product_id')
    def product_id_change(self):
        super().product_id_change()
        self.vendor_id = (
            self.product_id.seller_ids and self.product_id.seller_ids[0].name
            or False)
