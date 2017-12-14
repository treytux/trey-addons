# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields, api
from openerp.addons import decimal_precision as dp


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    price_unit_uos = fields.Float(
        string='UoS price unit',
        digits=dp.get_precision('Product Price'))
    price_unit_uos_old = fields.Float(
        string='Old UoS price unit',
        digits=dp.get_precision('Product Price'))
    price_unit_old = fields.Float(
        string='Old price unit',
        digits=dp.get_precision('Product Price'))

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
        prod = self.env['product.product'].browse(product)
        price = res_sale['value'].get('price_unit', 1)
        if not prod.price_unit_uos:
            res_sale['value'].update({
                'price_unit_old': price,
                'price_unit_uos': price,
                'price_unit_uos_old': price})
            return res_sale
        price_uos = prod.price_unit_uos * price / (prod.list_price or 1)
        res_sale['value'].update({
            'price_unit_old': price,
            'price_unit_uos': price_uos,
            'price_unit_uos_old': price_uos})
        return res_sale

    @api.onchange('price_unit')
    def onchange_price_unit(self):
        self.price_unit_uos = (
            self.price_unit * self.price_unit_uos_old / (
                self.price_unit_old or 1))

    @api.onchange('price_unit_uos')
    def onchange_price_unit_uos(self):
        self.price_unit = (
            self.price_unit_old * self.price_unit_uos / (
                self.price_unit_uos_old or 1))
