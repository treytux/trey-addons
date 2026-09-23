###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    def partner_for_goods_free(self):
        res = super().partner_for_goods_free()
        order = self.mapped('order_id')
        order.ensure_one()
        if order.partner_id.goods_free_ids:
            return res
        if order.partner_id.partner_group_id.goods_free_ids:
            return order.partner_id.partner_group_id
        return res
