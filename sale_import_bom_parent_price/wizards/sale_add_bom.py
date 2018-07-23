# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields, api


class SaleImportBoM(models.TransientModel):
    _inherit = 'wiz.sale_import_bom'

    price_in_parent = fields.Boolean(
        string='Price only in parent',
        default=True)

    @api.multi
    def get_data_order_line(self, product, qty):
        self.ensure_one()
        data = super(SaleImportBoM, self).get_data_order_line(product, qty)
        if self.env.context.get('parent') and self.price_in_parent:
            data['price_unit'] = 0
            data['parent_id'] = self.env.context.get('parent')
        return data

    @api.one
    def button_add(self):
        line = False
        if self.price_in_parent:
            data = self.get_data_order_line(
                self.bom_id.product_tmpl_id.product_variant_ids[0],
                self.quantity)
            line = self.env['sale.order.line'].create(data)
            self.only_import_products = True
        res = super(
            SaleImportBoM, self.with_context(
                parent=line and line.id or False)).button_add()
        return res

    @api.onchange('only_import_products')
    def onchange_only_import_products(self):
        if self.only_import_products:
            self.price_in_parent = False

    @api.onchange('price_in_parent')
    def onchange_price_in_parent(self):
        if self.price_in_parent:
            self.only_import_products = False
