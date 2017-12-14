# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.
from openerp import models, fields, api


class PackAdd(models.TransientModel):
    _name = 'wiz.sale_import_bom'
    _description = 'Import BoM to a sale order'

    order_id = fields.Many2one(
        comodel_name='sale.order',
        string='Order')
    bom_id = fields.Many2one(
        comodel_name='mrp.bom',
        string='BoM')
    quantity = fields.Float(
        string='Quantity',
        default=1)
    only_import_products = fields.Boolean(
        string='Only import products')

    @api.multi
    def get_data_order_line(self, product, qty):
        self.ensure_one()
        data = self.env['sale.order.line'].product_id_change(
            pricelist=self.order_id.pricelist_id.id, product=product.id,
            qty=qty, uom=product.uom_id.id, qty_uos=0, uos=False,
            name='', partner_id=self.order_id.partner_id.id, lang=False,
            update_tax=True, date_order=False, packaging=False,
            fiscal_position=self.order_id.fiscal_position.id,
            flag=False)['value']
        data['order_id'] = self.order_id.id
        data['product_id'] = product.id
        data['product_uom_qty'] = qty
        data['product_uom'] = product.uom_id.id
        if 'tax_id' in data:
            data['tax_id'] = [(6, 0, data['tax_id'])]
        return data

    @api.one
    def button_add(self):
        if not self.only_import_products:
            data = self.get_data_order_line(
                self.bom_id.product_tmpl_id.product_variant_ids[0],
                self.quantity)
            data['price_unit'] = 0
            self.env['sale.order.line'].create(data)
        for line in self.bom_id.bom_line_ids:
            data = self.get_data_order_line(
                line.product_id, self.quantity * line.product_qty)
            self.env['sale.order.line'].create(data)
        return {'type': 'ir.actions.act_window_close'}
