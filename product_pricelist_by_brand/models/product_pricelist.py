###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, models


class ProductPricelist(models.Model):
    _inherit = 'product.pricelist'

    @api.multi
    def _get_rules_sql(self, products, date):
        _select, _from, _where, _orderby, params = super()._get_rules_sql(
            products, date)
        brand_ids = [
            p.product_brand_id.id for p in products if p.product_brand_id]
        if not brand_ids:
            return _select, _from, _where, _orderby, params
        _where += (
            'AND (item.product_brand_id IS NULL '
            'OR item.product_brand_id = any(%s)) '
        )
        params.append(brand_ids)
        return _select, _from, _where, _orderby, params

    @api.multi
    def _is_valid_rule(self, rule, product, qty):
        is_valid = super()._is_valid_rule(rule, product, qty)
        if not is_valid:
            return is_valid
        if rule.product_brand_id:
            if product.product_brand_id != rule.product_brand_id:
                return False
        return is_valid
