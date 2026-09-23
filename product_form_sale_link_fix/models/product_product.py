###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from datetime import time, timedelta

from odoo import fields, models
from odoo.tools.float_utils import float_round


class ProductTemplate(models.Model):
    _inherit = 'product.product'

    def _compute_sales_count(self):
        r = {}
        if not self.user_has_groups('sales_team.group_sale_salesman'):
            return r
        date_from = fields.Datetime.to_string(fields.datetime.combine(
            fields.datetime.now() - timedelta(days=365), time.min))
        domain = [
            ('product_id', 'in', self.ids),
            ('date', '>=', date_from),
        ]
        for group in self.env['sale.report'].read_group(
                domain, ['product_id', 'product_uom_qty'], ['product_id']):
            r[group['product_id'][0]] = group['product_uom_qty']
        for product in self:
            product.sales_count = float_round(
                r.get(product.id, 0),
                precision_rounding=product.uom_id.rounding)
        return r
