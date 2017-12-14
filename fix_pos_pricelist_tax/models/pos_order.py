# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.
from openerp import models, api


class PosOrderLine(models.Model):
    _inherit = 'pos.order.line'

    @api.multi
    def onchange_product_id(self, pricelist, product_id, qty=0,
                            partner_id=False):
        result = super(PosOrderLine, self).onchange_product_id(
            pricelist=pricelist, product_id=product_id, qty=qty,
            partner_id=partner_id)
        if product_id:
            product = self.env['product.product'].browse(product_id)
            result['value']['tax_ids'] = product.product_tmpl_id.taxes_id
        return result
