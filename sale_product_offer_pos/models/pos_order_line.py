# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, api


class PosOrderLine(models.Model):
    _inherit = 'pos.order.line'

    @api.multi
    def onchange_product_id(
            self, pricelist, product_id, qty=0, partner_id=False):
        res = super(PosOrderLine, self).onchange_product_id(
            pricelist=pricelist, product_id=product_id, qty=qty,
            partner_id=partner_id)
        if not product_id:
            return res
        if not partner_id:
            offer_lines = self.env['product.offer'].get_product_offer(
                product_id=product_id)
        else:
            offer_lines = self.env['product.offer'].get_product_offer(
                customer_id=partner_id, product_id=product_id)
        if not offer_lines:
            return res
        if len(offer_lines) > 1:
            return res
        res['value'].update({'price_unit': offer_lines[0].price_unit})
        return res
