# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.
from openerp import models, fields, api


class InvoiceLinesEdit(models.TransientModel):
    _name = 'wiz.invoice_lines_edit'
    _description = 'Invoice lines edit'

    line_ids = fields.One2many(
        comodel_name='wiz.invoice_lines_edit.lines',
        inverse_name='wizard_id',
        string='Lines')

    @api.one
    def button_accept(self):
        for line in self.line_ids:
            line.line_id.write({
                'product_id': line.product_id.id,
                'quantity': line.quantity,
                'price_unit': line.price_unit,
                'discount': line.discount})
        return {'type': 'ir.actions.act_window_close'}


class InvoiceLinesEditLines(models.TransientModel):
    _name = 'wiz.invoice_lines_edit.lines'
    _description = 'Invoice lines edit, lines'

    wizard_id = fields.Many2one(
        comodel_name='wiz.invoice_lines_edit',
        string='Wizard')
    line_id = fields.Many2one(
        comodel_name='account.invoice.line',
        string='Invoice line')
    product_id = fields.Many2one(
        comodel_name='product.product',
        string='Product')
    quantity = fields.Float(string='Quantity')
    price_unit = fields.Float(string='Price Unit')
    discount = fields.Float(string='Discount')
