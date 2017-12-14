# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields, api, exceptions, _
import openerp.addons.decimal_precision as dp


class WizSaleDiscount(models.TransientModel):
    _name = 'wiz.sale.discount'
    _description = 'Apply discount to sale orders'

    name = fields.Char(
        string='Name')
    discount_type = fields.Selection(
        selection=[
            ('percent_line', 'Discount rate per line'),
            ('percent_total', 'Total discount percent'),
            ('quantity_total', 'Total discount quantity')],
        string='Discount type',
        default='percent_line',
        required=True)
    discount_applied = fields.Float(
        string='Discount applied (%)',
        digits_compute=dp.get_precision('Sale price'))
    product_id = fields.Many2one(
        comodel_name='product.product',
        string='Discount product')
    discount_quantity = fields.Float(
        string='Discount quantity')
    discount_taxes = fields.Many2many(
        comodel_name='account.tax',
        relation='sale_disc2tax_rel',
        column1='sale_discount_id',
        column2='tax_id',
        string='Discount taxes')

    @api.multi
    def button_accept(self):
        orders = self.env['sale.order'].browse(
            self.env.context.get('active_ids', []))
        for order in orders:
            if order.state != 'draft':
                raise exceptions.Warning(_(
                    'The discount can only be applied when sale orders are in '
                    '\'Draft\' state.'))
            if self.discount_type == 'percent_line':
                [line.write(
                    {'discount': self.discount_applied})
                 for line in order.order_line]
                order.button_dummy()
                continue
            if self.discount_type == 'percent_total':
                if self.discount_applied > 100 or self.discount_applied < 0:
                    raise exceptions.Warning(_(
                        'The applied discount must be between 0 and 100'))
            discount = order.amount_untaxed * (self.discount_applied / 100.0)
            price_unit = (
                -self.discount_quantity if
                self.discount_type == 'quantity_total' else -discount)
            line = self.env['sale.order.line'].create({
                'order_id': order.id,
                'product_id': self.product_id.id,
                'name': _('Discount line'),
                'price_unit': price_unit,
                'tax_id': [(6, 0, [tax.id for tax in self.discount_taxes])]})
            order.button_dummy()
        return {'type': 'ir.actions.act_window_close'}

    @api.onchange('product_id')
    def product_id_change(self):
        if self.product_id:
            self.discount_taxes = self.product_id.taxes_id
