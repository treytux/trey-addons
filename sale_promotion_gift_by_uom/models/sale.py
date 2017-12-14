# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.
from openerp import models, api
import logging
_log = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.model
    def _prepare_final_gift_product_data(self, gift_product):
        '''Inherit to add the same uom of promotion sale promotion gift.'''
        vals = super(SaleOrder, self)._prepare_final_gift_product_data(
            gift_product)
        vals.update({
            'uom_id': gift_product.uom_id and gift_product.uom_id.id or None})
        return vals

    @api.one
    @api.depends('order_line', 'order_line.offer_id')
    def _calc_sale_promotion_gifts(self):
        '''Inherit the function to apply gifts only when the unit of
        measurement of the sale order line and the pricelist item match.'''
        super(SaleOrder, self)._calc_sale_promotion_gifts()
        # Delete gift lines
        for gift in self.sale_promotion_gifts:
            self.sale_promotion_gifts = [(3, gift.id)]
        lines_with_price = self.order_line.filtered(lambda x: x.price_unit > 0)
        pricelist_item_obj = self.env['product.pricelist.item']
        for line in lines_with_price:
            # Get item id to apply
            res = self.pricelist_id.price_rule_get(
                line.product_id and line.product_id.id or None,
                line.product_uom_qty)
            item = pricelist_item_obj.browse(res.values()[0][1])
            # If the units of the sale order line and the pricelist item are
            # equal
            if not item.uom_id.exists() or line.product_uom == item.uom_id:
                # If gift does not exists, it is added
                if not self.sale_promotion_gifts.exists():
                    self.sale_promotion_gifts = [(
                        6, 0, line.offer_id.sale_promotion_gifts.mapped('id'))]
                #   Se supone que esto no hara falta cuando arreglen el
                # calculo de cantidades de regalos en la rama de gifts.
                # # If gift exists, the gifts are recalculated
                # else:
                #     sale_prom_gift = self.env['sale.promotion.gift'].browse(
                #         line.offer_id.sale_promotion_gifts.mapped('id'))
                #     sale_prom_gift.write({'qty': 3333})
