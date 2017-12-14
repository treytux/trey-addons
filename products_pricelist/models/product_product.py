# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields, api, _, exceptions


class ProductProduct(models.Model):
    _inherit = 'product.product'

    @api.multi
    def get_price_by_qty(self, pricelist_id, partner_id=None):
        self.ensure_one()
        pricelist = self.env['product.pricelist'].browse(pricelist_id)
        qtys = self.pricelist_minimal_qtys(pricelist, self)
        res = []
        prices = set()
        symbol = pricelist.currency_id.symbol
        for qty in qtys:
            item = pricelist.price_rule_get_multi(
                products_by_qty_by_partner=[(self, qty, partner_id)])
            price = item[self.id][pricelist.id][0]
            price = pricelist.currency_id.round(price)
            if price in prices or not price > 0:
                continue
            prices.add(price)
            res.append('%su-%s%s/u' % (qty, price, symbol))
        return [res[0]] if (len(qtys) > 1 and len(prices) == 1) else res

    @api.multi
    def pricelist_minimal_qtys(self, pricelist, product):
        def _get_pricelist_version(pricelist):
            date = fields.Datetime.now()
            for v in pricelist.version_id:
                if all([((v.date_start is False) or (v.date_start <= date)),
                        ((v.date_end is False) or (v.date_end >= date))]):
                    return v
            raise exceptions.Warning(
                _('No active version for pricelist %s') % pricelist.name)

        def _check_item(item, product):
            def check_is_parent_categ(item_categ, product_categ):
                if not item_categ or not product_categ:
                    return False
                if item_categ.id == product_categ.id:
                    return True
                if not product_categ.parent_id:
                    return False
                else:
                    return check_is_parent_categ(
                        item_categ, product_categ.parent_id)
            return any([
                check_is_parent_categ(item.categ_id, product.categ_id),
                item.product_tmpl_id.id == product.product_tmpl_id.id,
                item.product_id.id == product.id])
        res = []
        version = _get_pricelist_version(pricelist)
        for item in version.items_id:
            if item.base == -1:
                res += self.pricelist_minimal_qtys(
                    item.base_pricelist_id, product)
            if item.min_quantity != 0 and _check_item(item, product):
                res.append(item.min_quantity)
        return sorted(list(set(res)))
