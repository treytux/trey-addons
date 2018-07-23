# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields, api, exceptions, _


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    freight_product_id = fields.Many2one(
        comodel_name='product.product',
        string='Freight product')
    freight_price_unit = fields.Float(
        string='Freight price unit')
    penalty_product_id = fields.Many2one(
        comodel_name='product.product',
        string='Penalty product')
    penalty_price_unit = fields.Float(
        string='Penalty price unit')
    special_discount_product_id = fields.Many2one(
        comodel_name='product.product',
        string='Special discount product')
    special_discount_price_unit = fields.Float(
        string='Special discount price unit')

    @api.one
    @api.constrains('freight_price_unit')
    def _check_freight_price_unit(self):
        price_unit = self.freight_price_unit
        if price_unit > 0 and not self.freight_product_id.exists():
            raise exceptions.ValidationError(_(
                'You have not assigned any freight product, so the freight '
                'price unit must be zero.'))

    @api.one
    @api.constrains('penalty_price_unit')
    def _check_penalty_price_unit(self):
        price_unit = self.penalty_price_unit
        if price_unit > 0 and not self.penalty_product_id.exists():
            raise exceptions.ValidationError(_(
                'You have not assigned any penalty product, so the penalty '
                'price unit must be zero.'))

    @api.one
    @api.constrains('special_discount_price_unit')
    def _check_special_discount_price_unit(self):
        price_unit = self.special_discount_price_unit
        if price_unit > 0 and not self.special_discount_product_id.exists():
            raise exceptions.ValidationError(_(
                'You have not assigned any special discount product, so the '
                'special discount price unit must be zero.'))

    @api.multi
    def action_invoice_create(self, journal_id, group, type):

        def _get_account_id(self, invoice, product):
            if invoice.type in ('out_invoice', 'out_refund'):
                account = product.property_account_income
                if not account.exists():
                    account = product.categ_id.property_account_income_categ
            else:
                account = product.property_account_expense
                if not account.exists():
                    account = product.categ_id.property_account_expense_categ
            return self.env['account.fiscal.position'].map_account(account.id)

        def _get_tax_ids(self, invoice, product):
            if not self.move_lines:
                return []
            tax_obj = self.env['account.tax']
            one_move = self.move_lines[0]
            if ((self.picking_type_id.code == 'incoming' and
                    one_move.location_id.usage == 'supplier') or
                    (self.picking_type_id.code == 'outgoing' and
                     one_move.location_dest_id.usage == 'supplier')):
                tax_ids = [tax.id for tax in product.supplier_taxes_id]
            else:
                tax_ids = [tax.id for tax in product.taxes_id]
            taxes = tax_obj.browse(tax_ids)
            taxes = invoice.fiscal_position.map_tax(taxes)
            return taxes.ids

        invoice_ids = super(StockPicking, self).action_invoice_create(
            journal_id, group, type)
        if not invoice_ids:
            return invoice_ids
        data_list = []
        for picking in self:
            invoice = picking.invoice_ids and picking.invoice_ids[0] or None
            if not invoice:
                continue
            if picking.freight_product_id.exists():
                account_id = _get_account_id(
                    picking, invoice, picking.freight_product_id)
                tax_ids = _get_tax_ids(
                    picking, invoice, picking.freight_product_id)
                data_list.append({
                    'invoice_id': invoice.id,
                    'name': picking.freight_product_id.name,
                    'account_id': account_id,
                    'product_id': picking.freight_product_id.id,
                    'uos_id': (
                        picking.freight_product_id.uos_id and
                        picking.freight_product_id.uos_id.id or None),
                    'quantity': 1,
                    'price_unit': picking.freight_price_unit,
                    'invoice_line_tax_id': [(6, 0, tax_ids)]})
            if picking.penalty_product_id.exists():
                account_id = _get_account_id(
                    picking, invoice, picking.penalty_product_id)
                tax_ids = _get_tax_ids(
                    picking, invoice, picking.penalty_product_id)
                data_list.append({
                    'invoice_id': invoice.id,
                    'name': picking.penalty_product_id.name,
                    'account_id': account_id,
                    'product_id': picking.penalty_product_id.id,
                    'uos_id': (
                        picking.penalty_product_id.uos_id and
                        picking.penalty_product_id.uos_id.id or None),
                    'quantity': 1,
                    'price_unit': picking.penalty_price_unit,
                    'invoice_line_tax_id': [(6, 0, tax_ids)]})
            if picking.special_discount_product_id.exists():
                account_id = _get_account_id(
                    picking, invoice, picking.special_discount_product_id)
                tax_ids = _get_tax_ids(
                    picking, invoice, picking.special_discount_product_id)
                data_list.append({
                    'invoice_id': invoice.id,
                    'name': picking.special_discount_product_id.name,
                    'account_id': account_id,
                    'product_id': picking.special_discount_product_id.id,
                    'uos_id': (
                        picking.special_discount_product_id.uos_id and
                        picking.special_discount_product_id.uos_id.id or None),
                    'quantity': 1,
                    'price_unit': - picking.special_discount_price_unit,
                    'invoice_line_tax_id': [(6, 0, tax_ids)]})
        account_invoice_line_obj = self.env['account.invoice.line']
        for data in data_list:
            account_invoice_line_obj.create(data)
        return invoice_ids
