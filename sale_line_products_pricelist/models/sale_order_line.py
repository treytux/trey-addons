# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields, api


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    product_pricelist_qty = fields.Text(
        string='Promo')

    @api.multi
    def product_id_change_with_wh(
            self, pricelist, product, qty=0, uom=False, qty_uos=0, uos=False,
            name='', partner_id=False, lang=False, update_tax=True,
            date_order=False, packaging=False, fiscal_position=False,
            flag=False, warehouse_id=False):
        res = super(SaleOrderLine, self).product_id_change_with_wh(
            pricelist, product, qty=qty, uom=uom, qty_uos=qty_uos, uos=uos,
            name=name, partner_id=partner_id, lang=lang, update_tax=update_tax,
            date_order=date_order, packaging=packaging,
            fiscal_position=fiscal_position, flag=flag,
            warehouse_id=warehouse_id)
        if not product:
            return res
        product = self.env['product.product'].browse(product)
        text = product.get_price_by_qty(pricelist, partner_id)
        res['value']['product_pricelist_qty'] = '\n'.join(text or [])
        return res
