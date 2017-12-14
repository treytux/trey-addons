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

        if partner_id:
            partner = self.env['res.partner'].browse(partner_id)
            if not partner:
                return res
            partner_dto_group_id = partner.dto_group_id.id
        elif 'session_id' in self.env.context:
            session = self.env['pos.session'].browse(
                self.env.context['session_id'])
            partner_dto_group_id = session.config_id.dto_group_id.id
        else:
            return res

        product = self.env['product.product'].browse(product_id)
        groups = self.env['discount.group'].search([
            ('product_id', '=', product.dto_group_id.id),
            ('partner_id', '=', partner_dto_group_id)])
        if not groups:
            return res
        if 'value' not in res:
            res['value'] = {}

        # Comprobar si se debe de aplicar el grupo de descuento.
        # Una linea de tarifa puede ordenar que no se aplique el grupo de dto.
        pl = self.env['product.pricelist'].browse(pricelist)
        # qty = res['value']['product_uos_qty']
        price_rule = pl.price_rule_get(product.id, qty, partner=partner_id)
        rule = self.env['product.pricelist.item'].browse(
            price_rule[pricelist][1])
        if not rule.apply_discount_group:
            return res

        res['value']['discount'] = groups[0].discount
        return res
