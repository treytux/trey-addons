# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields, api, exceptions, _


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    offer_line_id = fields.Many2one(
        comodel_name='product.offer.line',
        string='Offer Line'
    )

    @api.multi
    def product_id_change(
            self, pricelist, product, qty=0, uom=False, qty_uos=0, uos=False,
            name='', partner_id=False, lang=False, update_tax=True,
            date_order=False, packaging=False, fiscal_position=False,
            flag=False):
        res_sale = super(SaleOrderLine, self).product_id_change(
            pricelist, product, qty=qty, uom=uom, qty_uos=qty_uos, uos=uos,
            name=name, partner_id=partner_id, lang=lang, update_tax=update_tax,
            date_order=date_order, packaging=packaging,
            fiscal_position=fiscal_position, flag=flag)
        if not product:
            return res_sale
        if not partner_id:
            return res_sale
        offer_lines = self.env['product.offer'].get_product_offer(
            customer_id=partner_id, product_id=product)
        if not offer_lines:
            return res_sale
        if len(offer_lines) > 1:
            raise exceptions.Warning(_(
                'You have defined more than one offer for this product that '
                'overlap. Please check'))
        res_sale['value'].update({
            'price_unit': offer_lines[0].price_unit,
            'offer_line_id': offer_lines[0].id,
        })
        return res_sale
