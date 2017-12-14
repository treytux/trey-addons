# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields, api


class SaleOrder(models.Model):
    _inherit = 'sale.order'
    matrix_ids = fields.One2many(
        comodel_name='sale.order.matrix',
        inverse_name='order_id',
        string='Matrix')


class SaleOrderMatrix(models.TransientModel):
    _name = 'sale.order.matrix'
    _description = 'Sale Order Matrix Colors and Sizes'

    order_id = fields.Many2one(
        comodel_name='sale.order',
        string='Order')
    product_tmpl_id = fields.Many2one(
        comodel_name='product.template',
        string='Product')
    value_ids = fields.One2many(
        comodel_name='sale.order.matrix.value',
        inverse_name='matrix_id',
        string='Values')
    total = fields.Float(
        string='Total',
        compute='_compute_total')

    @api.one
    @api.depends('value_ids')
    def _compute_total(self):
        self.total = sum([v.quantity for v in self.value_ids])

    @api.onchange('product_tmpl_id')
    def onchange_product_tmpl_id(self):
        attrs = [a for a in self.product_tmpl_id.attribute_line_ids]
        if len(attrs) < 2:
            return {'value': {'value_ids': [(6, 0, [])]}}

        value_ids = []
        for y_ids in attrs[0]:
            x_ids = attrs[1]
            value_ids.append({
                'product_tmpl_id': self.product_tmpl_id.id,
                'x_ids': [(6, 0, x_ids.ids)],
                'y_ids': [(6, 0, y_ids.ids)],
                'quantity': 0})
        return {
            'value': {
                'value_ids': value_ids
            }
        }


class SaleOrderMatrixValue(models.TransientModel):
    _name = 'sale.order.matrix.value'
    _description = 'Sale Order Matrix Colors and Sizes'

    matrix_id = fields.Many2one(
        comodel_name='sale.order.matrix',
        string='LABEL')
    x_ids = fields.Many2many(
        comodel_name='product.attribute',
        relation='product_attribute_sale_matrix_x_rel',
        column1='matrix_id',
        column2='attribute_id')
    y_ids = fields.Many2many(
        comodel_name='product.attribute',
        relation='product_attribute_sale_matrix_y_rel',
        column1='matrix_id',
        column2='attribute_id')
    quantity = fields.Float(string='Quantity')
