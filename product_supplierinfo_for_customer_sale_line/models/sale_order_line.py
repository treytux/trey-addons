# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, api, fields


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    default_code = fields.Char(
        string='Default Code')
    product_supplierinfo_id = fields.Many2one(
        comodel_name='product.supplierinfo',
        string='Customer Info',
        domain='[("type", "=", "customer"),'
               '("product_id", "=",product_id),'
               '("name", "=", parent.partner_id)]')
    default_code_customer = fields.Char(
        string='Default Code Customer')
    name_customer = fields.Char(
        string='Name Customer')

    @api.multi
    def product_id_change(
            self, pricelist, product, qty=0, uom=False, qty_uos=0, uos=False,
            name='', partner_id=False, lang=False, update_tax=True,
            date_order=False, packaging=False, fiscal_position=False,
            flag=False):
        res = super(SaleOrderLine, self).product_id_change(
            pricelist, product, qty=qty, uom=uom, qty_uos=qty_uos, uos=uos,
            name=name, partner_id=partner_id, lang=lang, update_tax=update_tax,
            date_order=date_order, packaging=packaging,
            fiscal_position=fiscal_position, flag=flag)
        if not product:
            return res
        prod = self.env['product.product'].browse(product)
        res['value']['default_code'] = prod.default_code
        infos = []
        for info in prod.customer_ids:
            if info.type != 'customer':
                continue
            if partner_id and partner_id != info.name.id:
                continue
            if info.product_id.id == product:
                infos = [info]
                break
            infos.append(info)
        if not infos:
            return res
        res['value']['product_supplierinfo_id'] = infos[0].id
        res['value']['default_code_customer'] = infos[0].product_code
        res['value']['name_customer'] = infos[0].product_name
        if res['value']['name_customer']:
            res['value']['name'] = res['value']['name_customer']
        if not infos[0].pricelist_ids:
            return res
        diff = 999999999999999999
        for line in infos[0].pricelist_ids:
            if line.min_quantity > qty:
                continue
            if qty - line.min_quantity > diff:
                continue
            res['value']['price_unit'] = line.price
            res['value']['discount'] = line.discount
            diff = qty - line.min_quantity
        return res

    @api.onchange('product_supplierinfo_id')
    def onchange_product_supplierinfo_id(self):
        for line in self:
            if not line.product_supplierinfo_id:
                return
            line.default_code_customer = (
                line.product_supplierinfo_id.product_code)
            line.name_customer = (
                line.product_supplierinfo_id.product_name)
            line.name = line.product_supplierinfo_id.product_name
