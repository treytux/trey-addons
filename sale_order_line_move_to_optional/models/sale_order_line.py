###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, models


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    @api.multi
    def move_to_optional(self):
        option_obj = self.env['sale.order.option']
        for line in self:
            option_obj.create({
                'order_id': line.order_id.id,
                'name': line.name,
                'product_id': line.product_id.id,
                'price_unit': line.price_unit,
                'sequence': line.sequence,
                'quantity': line.product_uom_qty,
                'uom_id': line.product_uom.id,
                'discount': line.discount,
            })
            line.unlink()
