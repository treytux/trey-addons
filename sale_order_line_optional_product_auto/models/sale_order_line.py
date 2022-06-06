###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, models


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    @api.onchange('product_id')
    def product_id_change(self):
        super().product_id_change()
        if self.product_id.product_tmpl_id.optional_product_method != 'auto':
            return
        to_unlink = self.order_id.sale_order_option_ids.filtered(
            lambda ln: ln.line_id == self)
        to_unlink.unlink()
        option_obj = self.env['sale.order.option']
        for template in self.product_id.optional_product_ids:
            option = option_obj.new({
                'order_id': self.order_id.id,
                'line_id': self.id,
                'product_id': template.product_variant_id.id,
                'name': template.name,
                'quantity': 1,
            })
            option._onchange_product_id()
            option_obj.create(option_obj._convert_to_write(option._cache))
