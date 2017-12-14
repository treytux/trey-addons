# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.

from openerp import models, api


class PosOrderLine(models.Model):
    _inherit = 'pos.order.line'

    @api.multi
    def onchange_product_id(self, pricelist, product_id, qty=0,
                            partner_id=False):
        res = super(PosOrderLine, self).onchange_product_id(
            pricelist, product_id, qty=qty, partner_id=partner_id)
        if not pricelist or not partner_id:
            return res
        sale_res = self.env['sale.order.line'].product_id_change(
            pricelist=pricelist,
            product=product_id, qty=qty or 0,
            uom=self.product_id.uom_id.id or False, qty_uos=0,
            uos=False, name='',
            partner_id=partner_id or False,
            lang=False, update_tax=True,
            date_order=False, packaging=False,
            fiscal_position=False, flag=False)
        if 'value' not in sale_res:
            return res
        sale_res = sale_res['value']
        if 'value' not in res:
            res['value'] = {}
        if 'discount' in sale_res:
            res['value']['discount'] = sale_res['discount']
        if 'price_unit' in sale_res:
            res['value']['price_unit'] = sale_res['price_unit']
        return res
