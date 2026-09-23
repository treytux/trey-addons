###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from datetime import timedelta

from odoo import fields, models
from odoo.tools.float_utils import float_round


class ProductProduct(models.Model):
    _inherit = 'product.product'

    def _compute_purchased_product_qty(self):
        date_from = fields.Datetime.to_string(
            fields.datetime.now() - timedelta(days=365))
        domain = [
            ('product_id', 'in', self.mapped('id')),
            ('date_order', '>', date_from),
        ]
        order_lines = self.env['purchase.order.line'].read_group(
            domain, ['product_id', 'product_uom_qty'], ['product_id'])
        purchased_data = dict([(
            data['product_id'][0],
            data['product_uom_qty']) for data in order_lines])
        for product in self:
            product.purchased_product_qty = float_round(
                purchased_data.get(product.id, 0),
                precision_rounding=product.uom_id.rounding)

    def action_view_po(self):
        res = super().action_view_po()
        res['domain'] = [('product_id', 'in', self.ids)]
        return res
