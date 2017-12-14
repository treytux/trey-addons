# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, api


class ProductProduct(models.Model):
    _inherit = 'product.product'

    @api.multi
    def get_price_by_qty(self, pricelist_id, partner_id=None):
        self.ensure_one()
        pricelist = self.env['product.pricelist'].browse(pricelist_id)
        qtys = self.pricelist_minimal_qtys(pricelist, self)
        res = []
        for qty in qtys:
            item = pricelist.price_rule_get_multi(
                products_by_qty_by_partner=[(self, qty, partner_id)])
            price_to_round = item[self.id][pricelist.id][0]
            price = pricelist.currency_id.round(price_to_round)
            res.append('%su-%s' % (qty, price))
        return res
