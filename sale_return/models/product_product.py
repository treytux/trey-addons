###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from datetime import time, timedelta

from odoo import api, fields, models
from odoo.tools.float_utils import float_round


class ProductProduct(models.Model):
    _inherit = 'product.product'

    def get_sales_domain_count(self, done_states, date_from):
        return [
            ('state', 'in', done_states),
            ('product_id', 'in', self.ids),
            ('date', '>=', date_from),
            ('is_return', '=', False),
        ]

    @api.multi
    def _compute_sales_count(self):
        res = super()._compute_sales_count()
        if (not res
                or not self.user_has_groups('sales_team.group_sale_salesman')):
            return res
        r = {}
        done_states = self.env['sale.report']._get_done_states()
        date_from = fields.Datetime.to_string(fields.datetime.combine(
            fields.datetime.now() - timedelta(days=365),
            time.min))
        domain = self.get_sales_domain_count(done_states, date_from)
        for group in self.env['sale.report'].read_group(
                domain, ['product_id', 'product_uom_qty'], ['product_id']):
            r[group['product_id'][0]] = group['product_uom_qty']
        for product in self:
            product.sales_count = float_round(
                r.get(product.id, 0),
                precision_rounding=product.uom_id.rounding)
        return r
