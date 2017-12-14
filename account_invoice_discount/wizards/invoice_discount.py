# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields, api, exceptions, _
import openerp.addons.decimal_precision as dp


class WizInvoiceDiscount(models.TransientModel):
    _name = 'wiz.invoice.discount'
    _description = 'Apply discount to account invoices'

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
        digits_compute=dp.get_precision('Account'))
    product_id = fields.Many2one(
        comodel_name='product.product',
        string='Discount product')
    discount_quantity = fields.Float(
        string='Discount quantity')
    discount_tax_ids = fields.Many2many(
        comodel_name='account.tax',
        relation='sale_discount2tax_rel',
        column1='inv_discount_id',
        column2='tax_id')

    @api.multi
    def button_accept(self):
        invoices = self.env['account.invoice'].browse(
            self.env.context.get('active_ids', []))
        for invoice in invoices:
            if invoice.state != 'draft':
                raise exceptions.Warning(_(
                    'The discount can only be applied when invoices are in '
                    '\'Draft\' state.'))
            if self.discount_type == 'percent_line':
                for line in invoice.invoice_line:
                    line.write({
                        'discount': self.discount_applied})
                invoice.button_reset_taxes()
            tax_ids = [tax.id for tax in self.discount_tax_ids]
            if self.discount_type == 'percent_total':
                if self.discount_applied > 100 or self.discount_applied < 0:
                    raise exceptions.Warning(_(
                        'The applied discount must be between 0 and 100'))
                discount = invoice.amount_untaxed * \
                    (self.discount_applied / 100.0)
                line = self.env['account.invoice.line'].create({
                    'account_id': invoice.account_id.id,
                    'invoice_id': invoice.id,
                    'invoice_line_tax_id': [(6, 0, tax_ids)],
                    'name': _('Discount line'),
                    'price_unit': -discount,
                    'product_id': self.product_id.id,
                    'quantity': 1.0})
                invoice.button_reset_taxes()
            if self.discount_type == 'quantity_total':
                line = self.env['account.invoice.line'].create({
                    'account_id': invoice.account_id.id,
                    'invoice_id': invoice.id,
                    'invoice_line_tax_id': [(6, 0, tax_ids)],
                    'name':  _('Discount line'),
                    'price_unit': -self.discount_quantity,
                    'product_id': self.product_id.id,
                    'quantity': 1.0})
                invoice.button_reset_taxes()
        return {'type': 'ir.actions.act_window_close'}

    @api.onchange('product_id')
    def onchange_product_id(self):
        if self.product_id:
            self.discount_tax_ids = self.product_id.taxes_id
