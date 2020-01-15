###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, models, _
from odoo.exceptions import UserError


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    def _check_line_min_order_qty(self):
        for line in self:
            if not line.product_id:
                return
            if line.product_uom_qty < line.product_id.min_order_qty:
                raise UserError(_(
                    'Product "%s" has minimum order qty to %s and you order '
                    '%s, please increase the quantity') % (
                        line.product_id.name, line.product_id.min_order_qty,
                        line.product_uom_qty))

    @api.model
    def create(self, vals):
        line = super().create(vals)
        line._check_line_min_order_qty()
        return line

    @api.multi
    def write(self, vals):
        re = super().write(vals)
        self._check_line_min_order_qty()
        return re

    @api.onchange('product_uom', 'product_uom_qty')
    def product_uom_change(self):
        super().product_uom_change()
        self._check_line_min_order_qty()
