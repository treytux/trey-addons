from odoo import models
from odoo.http import request


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def _cart_update(
        self, product_id=None, line_id=None, add_qty=0, set_qty=0, **kwargs
    ):
        self.ensure_one()
        order = self
        sect_type = 'line_section'
        values = super()._cart_update(
            product_id=product_id,
            line_id=line_id,
            add_qty=add_qty,
            set_qty=set_qty,
            **kwargs
        )
        order = request.website.sale_get_order()
        if not order:
            return values
        sections = order.order_line.filtered(
            lambda ln: not ln.product_id.active and ln.display_type == sect_type
        )
        if sections:
            if values.get('line_id') and not line_id:
                new_line = order.order_line.browse(values['line_id'])
                if new_line.exists() and not new_line.display_type:
                    min_seq = min(sections.mapped('sequence') or [100])
                    new_line.sequence = min_seq - 1
            order.website_order_line = order.order_line.sorted('sequence')
        return values
