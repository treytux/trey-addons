###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.depends('order_line', 'order_line.product_uom_qty',
                 'order_line.price_subtotal')
    def _compute_goods_free_amount_total(self):
        res = super()._compute_goods_free_amount_total()
        for sale in self:
            precision = sale.order_line._fields['price_unit'].digits[1]
            lines = sale.order_line.filtered(lambda ln: ln.line_goods_free_id)
            goods_free = self.env['res.partner.goods_free']
            if sale.partner_id.goods_free_ids:
                goods_free = sale.partner_id.goods_free_ids
            elif sale.partner_id.partner_group_id.goods_free_ids:
                goods_free = sale.partner_group_id.goods_free_ids
            total = 0
            for line in lines:
                agreement = goods_free.filtered(
                    lambda g: g.product_id == line.product_id)
                qty_goods = line.line_goods_free_id.product_uom_qty
                total += round(
                    qty_goods * (agreement.percent / 100) * line.price_unit,
                    precision)
            sale.goods_free_amount_pending = (
                total - sale.goods_free_amount_total)
        return res

    def action_recompute_goods_free(self):
        self.ensure_one()
        lines_free = self.order_line.filtered(
            lambda ln: ln.line_goods_free_id)
        precision = self.order_line._fields['price_unit'].digits[1]
        total_free = 0
        total_assigned = 0
        goods_free = self.env['res.partner.goods_free']
        if self.partner_id.goods_free_ids:
            goods_free = self.partner_id.goods_free_ids
        elif self.partner_id.partner_group_id.goods_free_ids:
            goods_free = self.partner_group_id.goods_free_ids
        for line in lines_free:
            agreement = goods_free.filtered(
                lambda g: g.product_id == line.product_id)
            qty_goods = line.line_goods_free_id.product_uom_qty
            qty_real = qty_goods * (agreement.percent / 100)
            line.product_uom_qty = int(qty_real)
            total_free += round(qty_real * line.price_unit, precision)
            total_assigned += round(int(qty_real) * line.price_unit, precision)
        pending_to_assign = total_free - total_assigned
        lines_free = lines_free.sorted('price_unit', reverse=True)
        while lines_free:
            for line in lines_free:
                if line.price_unit > pending_to_assign:
                    continue
                line.product_uom_qty += 1
                pending_to_assign -= line.price_unit
            lines_free = lines_free.filtered(
                lambda ln: ln.price_unit <= pending_to_assign)
