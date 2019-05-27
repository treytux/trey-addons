# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields, api


class SaleOrderLineEdit(models.TransientModel):
    _name = 'wiz.sale_order_line_edit'
    _description = 'Sale order lines edit'

    line_ids = fields.One2many(
        comodel_name='wiz.sale_order_line_edit.lines',
        inverse_name='wizard_id',
        string='Lines')
    picking_id = fields.Many2one(
        comodel_name='stock.picking',
        string='Picking')

    @api.one
    def button_accept(self):
        for line in self.line_ids:
            line.line_id.write({
                'product_id': line.product_id.id,
                'name': line.name,
                'product_uom_qty': line.quantity,
                'price_unit': line.price_unit,
                'discount': line.discount})
        return {'type': 'ir.actions.act_window_close'}


class SaleOrderLineEditLines(models.TransientModel):
    _name = 'wiz.sale_order_line_edit.lines'
    _description = 'Lines of sale order lines edit'

    wizard_id = fields.Many2one(
        comodel_name='wiz.sale_order_line_edit',
        string='Wizard')
    line_id = fields.Many2one(
        comodel_name='sale.order.line',
        string='Sale order line')
    line_name_origin = fields.Char(
        string='Origin line name')
    product_id = fields.Many2one(
        comodel_name='product.product',
        string='Product')
    quantity = fields.Float(string='Quantity')
    price_unit = fields.Float(string='Price Unit')
    discount = fields.Float(string='Discount')
    name = fields.Text(string='Description')
