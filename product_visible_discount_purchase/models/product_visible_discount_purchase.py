# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.
from openerp import models, api


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    @api.multi
    def onchange_product_id(
            self, pricelist_id, product_id, qty, uom_id, partner_id,
            date_order=False, fiscal_position_id=False, date_planned=False,
            name=False, price_unit=False, state='draft'):
        res = super(PurchaseOrderLine, self).onchange_product_id(
            pricelist_id, product_id, qty, uom_id, partner_id,
            date_order=date_order, fiscal_position_id=fiscal_position_id,
            date_planned=date_planned, name=name, price_unit=price_unit,
            state=state)

        def get_real_price_curency(res_dict, product_id, qty, uom, pricelist):
            '''Retrieve the price before applying the pricelist.'''
            item_obj = self.env['product.pricelist.item']
            price_type_obj = self.env['product.price.type']
            product_obj = self.env['product.product']
            product_uom_obj = self.env['product.uom']
            field_name = 'list_price'
            rule_id = (res_dict.get(pricelist) and
                       res_dict[pricelist][1] or False)
            currency_id = None
            if rule_id:
                rule = item_obj.browse(rule_id)
                if rule.base > 0:
                    price_type = price_type_obj.browse(rule.base)
                    field_name = price_type.field
                    currency_id = price_type.currency_id
            product = product_obj.browse(product_id)
            product_read = product.read([field_name])
            if not currency_id:
                currency_id = product.company_id.currency_id.id
            factor = 1.0
            if uom and uom != product.uom_id.id:
                # the unit price is in a different uom
                factor = product_uom_obj._compute_qty(
                    uom, 1.0, product.uom_id.id)
            return product_read[0][field_name] * factor, currency_id

        def get_real_price(res_dict, product_id, qty, uom, pricelist):
            return get_real_price_curency(
                res_dict, product_id, qty, uom, pricelist)[0]

        result = res['value']
        pricelist_obj = self.env['product.pricelist']
        product_obj = self.env['product.product']
        users_obj = self.env['res.users']
        if product_id and pricelist_id and users_obj.has_group(
                'sale.group_discount_per_so_line'):
            if result.get('price_unit', False):
                price = result['price_unit']
            else:
                return res
            product = product_obj.browse(product_id)
            uom = product.uom_id and product.uom_id.id or None
            pricelist = pricelist_obj.browse(pricelist_id)
            list_price = pricelist.price_rule_get(
                product.id, qty or 1.0, partner_id)
            new_list_price, currency_id = get_real_price_curency(
                list_price, product.id, qty, uom, pricelist_id)
            if (pricelist.visible_discount and
                    list_price[pricelist_id][0] != 0 and new_list_price != 0):
                if (product.company_id and
                        pricelist.currency_id.id !=
                        product.company_id.currency_id.id):
                    new_list_price = currency_id.compute(
                        new_list_price, pricelist.currency_id)
                discount = (new_list_price - price) / new_list_price * 100
                if discount > 0:
                    result['price_unit'] = new_list_price
                    result['discount'] = discount
                else:
                    result['discount'] = 0.0
            else:
                result['discount'] = 0.0
        else:
            result['discount'] = 0.0
        return res


class ProcurementOrder(models.Model):
    _inherit = 'procurement.order'

    @api.multi
    def make_po(self):
        res = super(ProcurementOrder, self).make_po()
        order_lines = self.env['purchase.order.line'].browse(res.values())
        for line in order_lines:
            values = self.env['purchase.order.line'].onchange_product_id(
                line.order_id.pricelist_id.id,
                line.product_id.id,
                line.product_qty,
                line.product_uom.id,
                line.partner_id.id,
                date_order=line.date_order,
                fiscal_position_id=line.order_id.fiscal_position.id,
                date_planned=line.date_planned,
                name=line.name)
            if values:
                data = {'price_unit': values['value']['price_unit']}
                if 'discount' in values['value']:
                    data.update({'discount': values['value']['discount']})
                line.write(data)
        return res
