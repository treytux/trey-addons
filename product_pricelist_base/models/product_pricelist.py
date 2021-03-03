###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from itertools import chain

from odoo import api, fields, models, tools
from odoo.exceptions import UserError


class ProductPricelist(models.Model):
    _inherit = 'product.pricelist'

    @api.multi
    def _get_rules_sql(self, products, date):
        self.ensure_one()
        categ_ids = set([])
        for product in products:
            categ = product.categ_id
            while categ:
                categ_ids.add(categ.id)
                categ = categ.parent_id
        categ_ids = list(categ_ids)
        if products[0]._name == 'product.template':
            prod_tmpl_ids = [p.id for p in products]
            prod_ids = [
                p.id
                for p in list(chain.from_iterable(
                    [t.product_variant_ids for t in products]
                ))
            ]
        else:
            prod_tmpl_ids = [p.product_tmpl_id.id for p in products]
            prod_ids = [p.id for p in products]

        _select = 'SELECT item.id '
        _from = (
            'FROM product_pricelist_item AS item '
            'LEFT JOIN product_category AS categ '
            'ON item.categ_id = categ.id '
        )
        _where = (
            'WHERE '
            '(item.product_tmpl_id IS NULL OR item.product_tmpl_id = any(%s))'
            'AND (item.product_id IS NULL OR item.product_id = any(%s))'
            'AND (item.categ_id IS NULL OR item.categ_id = any(%s)) '
            'AND (item.pricelist_id = %s) '
            'AND (item.date_start IS NULL OR item.date_start<=%s) '
            'AND (item.date_end IS NULL OR item.date_end>=%s)'
        )
        _orderby = (
            'ORDER BY '
            'item.applied_on, item.min_quantity desc, '
            'categ.complete_name desc, item.id desc'
        )
        return (
            _select, _from, _where, _orderby,
            [prod_tmpl_ids, prod_ids, categ_ids, self.id, date, date]
        )

    @api.multi
    def _is_valid_rule(self, rule, product, qty):
        self.ensure_one()
        if rule.min_quantity and qty < rule.min_quantity:
            return False
        if product._name == 'product.template':
            if rule.product_tmpl_id and product.id != rule.product_tmpl_id.id:
                return False
            if rule.product_id and not (
                    product.product_variant_count == 1
                    and product.product_variant_id.id == rule.product_id.id):
                return False
        else:
            if (rule.product_tmpl_id
                    and product.product_tmpl_id.id != rule.product_tmpl_id.id):
                return False
            if rule.product_id and product.id != rule.product_id.id:
                return False
        if rule.categ_id:
            cat = product.categ_id
            while cat:
                if cat.id == rule.categ_id.id:
                    break
                cat = cat.parent_id
            if not cat:
                return False
        return True

    def _price_get(self, product, rule=None, qty=None, partner=None, date=None):
        if self._context.get('force_price'):
            return self._context['force_price']
        if not rule:
            return product.price_compute('list_price')[product.id]
        if rule.base == 'pricelist' and rule.base_pricelist_id:
            price_tmp = rule.base_pricelist_id._compute_price_rule(
                [(product, qty, partner)])[product.id][0]
            return rule.base_pricelist_id.currency_id._convert(
                price_tmp, self.currency_id, self.env.user.company_id,
                date, round=False)
        return product.price_compute(rule.base)[product.id]

    @api.multi
    def _apply_formula(self, rule, product, price, price_uom):
        convert_to_price_uom = (
            lambda price: product.uom_id._compute_price(price, price_uom))
        if rule.compute_price == 'fixed':
            price = convert_to_price_uom(rule.fixed_price)
        elif rule.compute_price == 'percentage':
            price = ((price - (price * (rule.percent_price / 100))) or 0.0)
        elif rule.compute_price == 'formula':
            price_limit = price
            price = ((price - (price * (rule.price_discount / 100))) or 0.0)
            if rule.price_round:
                price = tools.float_round(
                    price, precision_rounding=rule.price_round)
            if rule.price_surcharge:
                price_surcharge = convert_to_price_uom(rule.price_surcharge)
                price += price_surcharge
            if rule.price_min_margin:
                price_min_margin = convert_to_price_uom(rule.price_min_margin)
                price = max(price, price_limit + price_min_margin)
            if rule.price_max_margin:
                price_max_margin = convert_to_price_uom(rule.price_max_margin)
                price = min(price, price_limit + price_max_margin)
        return price

    @api.multi
    def _compute_rule(self, items, date, product, qty, partner):
        suitable_rule = False
        qty_uom_id = self._context.get('uom') or product.uom_id.id
        qty_in_product_uom = qty
        if qty_uom_id != product.uom_id.id:
            try:
                qty_in_product_uom = self.env['uom.uom'].browse(
                    [self._context['uom']])._compute_quantity(
                        qty, product.uom_id)
            except UserError:
                pass
        price = self._price_get(product)
        price_uom = self.env['uom.uom'].browse([qty_uom_id])
        for rule in items:
            is_valid = self._is_valid_rule(
                rule, product, qty_in_product_uom)
            if not is_valid:
                continue
            price = self._price_get(
                product, rule=rule, qty=qty, partner=partner, date=date)
            if price is not False:
                price = self._apply_formula(rule, product, price, price_uom)
                suitable_rule = rule
            break
        if (suitable_rule
                and suitable_rule.compute_price != 'fixed'
                and suitable_rule.base != 'pricelist'):
            if suitable_rule.base == 'standard_price':
                cur = product.cost_currency_id
            else:
                cur = product.currency_id
            price = cur._convert(
                price, self.currency_id, self.env.user.company_id,
                date, round=False)
        return (price, suitable_rule and suitable_rule.id or False)

    @api.multi
    def _compute_price_rule(self, products_qty_partner,
                            date=False, uom_id=False):
        self.ensure_one()
        if not date:
            date = self._context.get('date') or fields.Date.context_today(self)
        if not uom_id and self._context.get('uom'):
            uom_id = self._context['uom']
        if uom_id:
            products = [
                item[0].with_context(uom=uom_id)
                for item in products_qty_partner]
            products_qty_partner = [
                (products[index], data_struct[1], data_struct[2])
                for index, data_struct in enumerate(products_qty_partner)]
        else:
            products = [item[0] for item in products_qty_partner]
        if not products:
            return {}
        _select, _from, _where, _orderby, params = self._get_rules_sql(
            products, date)
        self._cr.execute(' '.join([_select, _from, _where, _orderby]), params)
        item_ids = [x[0] for x in self._cr.fetchall()]
        items = self.env['product.pricelist.item'].browse(item_ids)
        results = {}
        for product, qty, partner in products_qty_partner:
            results[product.id] = 0.0
            results[product.id] = self._compute_rule(
                items, date, product, qty, partner)
        return results
