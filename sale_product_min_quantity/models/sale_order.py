# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.
from openerp import models, fields, api


class ProductProduct(models.Model):
    _inherit = 'product.template'

    sale_min_quantity = fields.Float(string='Min Qty', default=1)
    sale_multiple_quantity = fields.Float(string='Multiple Qty')


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    @api.multi
    def product_id_change(
            self, pricelist, product, qty=0, uom=False, qty_uos=0, uos=False,
            name='', partner_id=False, lang=False, update_tax=True,
            date_order=False, packaging=False, fiscal_position=False,
            flag=False):
        prod = self.env['product.product'].browse(product)
        minimun = prod.sale_min_quantity
        multiple = prod.sale_multiple_quantity
        if minimun and minimun > qty:
            qty = minimun
        if multiple and qty % multiple != 0:
            qty = (int(qty / multiple) + 1) * multiple

        res = super(SaleOrderLine, self).product_id_change(
            pricelist, product, qty=qty, uom=uom, qty_uos=qty_uos, uos=uos,
            name=name, partner_id=partner_id, lang=lang, update_tax=update_tax,
            date_order=date_order, packaging=packaging,
            fiscal_position=fiscal_position, flag=flag)
        res['value']['product_uom_qty'] = qty
        return res
