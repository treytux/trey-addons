# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.
from openerp import models, api
import logging
_log = logging.getLogger(__name__)


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    @api.multi
    def product_id_change(self, pricelist, product, qty=0,
                          uom=False, qty_uos=0, uos=False, name='',
                          partner_id=False, lang=False, update_tax=True,
                          date_order=False, packaging=False,
                          fiscal_position=False, flag=False):
        res = super(SaleOrderLine, self).product_id_change(
            pricelist, product, qty=qty, uom=uom, qty_uos=qty_uos, uos=uos,
            name=name, partner_id=partner_id, lang=lang, update_tax=update_tax,
            date_order=date_order, packaging=packaging,
            fiscal_position=fiscal_position, flag=flag)

        if not product:
            return res

        partner = self.env['res.partner'].browse(partner_id)
        if not partner:
            return res

        product = self.env['product.product'].browse(product)
        if not product:
            return res

        groups = self.env['discount.group'].search([
            ('product_id', '=', product.dto_group_id.id),
            ('partner_id', '=', partner.dto_group_id.id)])
        if not groups:
            return res

        # Comprobar si se debe de aplicar el grupo de descuento.
        # Una linea de tarifa puede ordenar que no se aplique el grupo de dto.
        pl = self.env['product.pricelist'].browse(pricelist)
        qty = res['value']['product_uos_qty']
        price_rule = pl.price_rule_get(product.id, qty, partner=partner.id)
        rule = self.env['product.pricelist.item'].browse(
            price_rule[pricelist][1])
        if not rule.apply_discount_group:
            return res

        res['value']['discount'] = groups[0].discount
        return res
