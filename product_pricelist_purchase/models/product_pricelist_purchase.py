###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class ProductPricelistPurchase(models.Model):
    _name = 'product.pricelist.purchase'
    _inherit = ['product.pricelist']

    def _get_default_item_ids(self):
        ProductPricelistItem = self.env['product.pricelist.item']
        vals = ProductPricelistItem.default_get(
            list(ProductPricelistItem._fields))
        vals.update(compute_price='formula')
        return [[0, False, vals]]

    item_ids = fields.One2many(
        comodel_name='product.pricelist.item',
        inverse_name='purchase_pricelist_id',
        string='Pricelist Items',
        copy=True,
        default=_get_default_item_ids,
    )

    def _price_get(self, product, rule=None, qty=None, partner=None,
                   date=None):
        if (rule and rule.base == 'purchase_price'
                and 'ref_price' in self._context):
            return self._context['ref_price']
        return super()._price_get(
            product, rule=rule, qty=qty, partner=partner, date=date)

    def _get_rules_sql(self, products, date):
        _select, _from, _where, _orderby, params = super()._get_rules_sql(
            products, date)
        _where = _where.replace(
            'AND (item.pricelist_id = %s) ',
            'AND (item.purchase_pricelist_id = %s) ')
        return (_select, _from, _where, _orderby, params)
