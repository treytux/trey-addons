# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields, api, _


class WizUpdateProductPrice(models.TransientModel):
    _name = 'wiz.update_product_price'

    name = fields.Char(
        string='Name')
    wiz_line_ids = fields.Many2many(
        comodel_name='wiz.update_product_price_line',
        relation='update_product_update_line_rel',
        column1='update_product_price',
        column2='update_product_price_line')

    @api.multi
    def button_purchase_view(self):
        product_ids = self.env.context.get('active_ids', [])
        self.wiz_line_ids = [(6, 0, [])]
        wiz_products = []
        for product in self.env['product.product'].browse(product_ids):
            if product.bom_count == 0:
                continue
            bom = (len(product.bom_ids) == 1 and product.bom_ids[0] or
                   sorted(product.bom_ids, key=lambda bom: bom.sequence)[0])
            wiz_products.append((0, 0, {
                'product_id': product.id,
                'standard_price': product.standard_price,
                'new_standard_price': '%.2f' % bom.bom_prod_price_total}))
        self.wiz_line_ids = wiz_products
        view = self.env.ref(
            'product_standard_price_update_wiz.wiz_update_price_create_ok')
        return {
            'name': _('Products to update'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'wiz.update_product_price',
            'view_id': view.id,
            'res_id': self.id,
            'target': 'new',
            'views': False,
            'type': 'ir.actions.act_window',
            'context': self.env.context}

    @api.multi
    def button_apply_standard_price(self):
        for line in self.wiz_line_ids:
            product = self.env['product.product'].browse(line.product_id.id)
            product.write({'standard_price': line.new_standard_price,
                           'list_price': line.list_price})


class WizUpdateProductPriceLine(models.TransientModel):
    _name = 'wiz.update_product_price_line'

    name = fields.Char(
        string='Name')
    product_id = fields.Many2one(
        comodel_name='product.product',
        string='Product Variant',
        readonly=True)
    list_price = fields.Float(
        related='product_id.list_price',
        string='Price')
    standard_price = fields.Float(
        string='Cost price')
    new_standard_price = fields.Float(
        string='new cost price')
