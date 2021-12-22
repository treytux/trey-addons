###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models


class ProductPricelist(models.Model):
    _inherit = 'product.pricelist'

    def _get_price_by_condition(self, price, rule):
        for condition in rule.condition_ids:
            if price >= condition.price_from and price <= condition.price_to:
                return price * condition.percent_increase / 100
        return price

    def _compute_price_rule(
            self, products_qty_partner, date=False, uom_id=False):
        res = super()._compute_price_rule(products_qty_partner, date, uom_id)
        rule_obj = self.env['product.pricelist.item']
        for product, _qty, _partner in products_qty_partner:
            rule = rule_obj.browse(res[product.id][1])
            if rule.compute_price == 'condition':
                res[product.id] = (
                    self._get_price_by_condition(res[product.id][0], rule),
                    rule.id)
        return res
