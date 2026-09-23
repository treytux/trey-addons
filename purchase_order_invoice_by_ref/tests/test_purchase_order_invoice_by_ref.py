###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields
from odoo.tests import common


class TestPurchaseOrderInvoiceByRef(common.TransactionCase):

    def setUp(self):
        super().setUp()
        self.product_service = self.env['product.product'].create({
            'type': 'service',
            'company_id': False,
            'name': 'Product service test',
            'standard_price': 10,
            'purchase_method': 'receive',
        })
        self.product_stock_01 = self.env['product.product'].create({
            'type': 'product',
            'company_id': False,
            'name': 'Product test purchase method 1',
            'standard_price': 10,
            'purchase_method': 'purchase',
        })
        self.product_stock_02 = self.env['product.product'].create({
            'type': 'product',
            'company_id': False,
            'name': 'Product test purchase method 2',
            'standard_price': 10,
            'purchase_method': 'purchase',
        })
        self.partner = self.env['res.partner'].create({
            'name': 'Test partner',
        })
        self.journal = self.env['account.journal'].create({
            'company_id': self.env.company.id,
            'type': 'purchase',
            'name': 'Debts',
            'code': 'DBT',
        })
        self.account_receiv = self.env['account.account'].create({
            'name': 'Receivable',
            'code': 'RCV00',
            'account_type': 'asset_receivable',
            'reconcile': True,
        })
        self.account_payable = self.env['account.account'].create({
            'code': 'NC1110',
            'name': 'Test Payable',
            'account_type': 'liability_payable',
            'reconcile': True,
        })
        self.partner.property_account_payable_id = self.account_payable
        self.partner.property_account_receivable_id = self.account_receiv
        category_all = self.env.ref('product.product_category_all')
        self.account_expense = self.env['account.account'].create({
            'code': 'EXP01TEST',
            'name': 'Test expense',
            'account_type': 'expense',
            'reconcile': True,
        })
        category_all.property_account_expense_categ_id = self.account_expense
        self.account_income = self.env['account.account'].create({
            'code': 'REV01TEST',
            'name': 'Account revenue test',
            'account_type': 'income',
            'reconcile': True,
        })
        category_all.property_account_income_categ_id = self.account_income

    def create_purchase(self, ref, product):
        purchase = self.env['purchase.order'].create({
            'partner_id': self.partner.id,
            'partner_ref': ref,
        })
        line_obj = self.env['purchase.order.line']
        line = line_obj.new({
            'order_id': purchase.id,
            'product_id': product.id,
            'product_uom_qty': 1,
        })
        line.onchange_product_id()
        line['price_unit'] = 100
        line_obj.create(line_obj._convert_to_write(line._cache))
        purchase.button_confirm()
        return purchase

    def test_purchase_order(self):
        refs = ['01', '*-02-*', '03...']
        purchases = self.env['purchase.order'].browse([])
        for ref in refs:
            purchases |= self.create_purchase(ref, self.product_service)
        self.assertEqual(len(purchases), 3)
        wizard = self.env['purchase.order.invoice_refs'].create({
            'partner_id': self.partner.id,
            'references': '\n'.join(refs),
            'method': 'all',
            'join_purchases': True,
        })
        self.assertEqual(wizard.partner_id, self.partner)
        self.assertFalse(
            [e for e in wizard.references_to_list() if e not in refs])
        wizard.find_purchases()
        self.assertEqual(wizard.partner_id, self.partner)
        self.assertEqual(purchases, wizard.purchase_ids)
        wizard.references = '01 \n *-02-* \n 03...\n   \n \n'
        wizard.find_purchases()
        self.assertEqual(purchases, wizard.purchase_ids)
        self.assertEqual(len(wizard.line_ids), 0)
        purchase = self.create_purchase('01', self.product_service)
        wizard.find_purchases()
        self.assertNotEqual(purchases, wizard.purchase_ids)
        self.assertEqual(len(wizard.line_ids), 1)
        self.assertIn('01', wizard.line_ids.ref)
        self.assertIn('Return more than one purchase.', wizard.line_ids.name)
        self.assertEqual(wizard.line_ids.type, 'error')
        purchase.button_cancel()
        purchase.unlink()
        wizard.line_ids.unlink()
        wizard.references = '01\n01\n01\n*-02-*\n03...\n04'
        wizard.find_purchases()
        self.assertEqual(len(wizard.references_to_list()), 6)
        self.assertEqual(purchases, wizard.purchase_ids)
        self.assertEqual(len(wizard.line_ids), 3)
        self.assertIn('01', wizard.line_ids[0].ref)
        self.assertIn(
            'Reference duplicate, ignore one.', wizard.line_ids[0].name)
        self.assertEqual(wizard.line_ids[0].type, 'warning')
        self.assertIn('01', wizard.line_ids[1].ref)
        self.assertIn(
            'Reference duplicate, ignore one.', wizard.line_ids[1].name)
        self.assertEqual(wizard.line_ids[1].type, 'warning')
        self.assertIn('04', wizard.line_ids[2].ref)
        self.assertIn('Purchase not found.', wizard.line_ids[2].name)
        self.assertEqual(wizard.line_ids[2].type, 'error')
        wizard.references = '01\n*-02-*\n03...\n'
        wizard.action_find()
        self.assertEqual(purchases, wizard.purchase_ids)
        wizard.action_invoice()
        self.assertEqual(len(purchases[0].invoice_ids), 1)

    def test_purchase_order_with_taxes(self):
        company = self.env.company
        country = company.account_fiscal_country_id or company.country_id
        if not country:
            country = self.env['res.country'].search([], limit=1)
            self.env.company.write({'country_id': country.id})
        tax_group_taxes = self.env.ref('account.tax_group_taxes')
        tax = self.env['account.tax'].create({
            'name': 'Tax for purchase 10%',
            'type_tax_use': 'purchase',
            'tax_group_id': tax_group_taxes.id,
            'amount_type': 'percent',
            'amount': 10.0,
            'country_id': country.id,
        })
        self.product_service.supplier_taxes_id = [(6, 0, tax.ids)]
        refs = ['01', '*-02-*', '03...']
        purchases = self.env['purchase.order'].browse([])
        for ref in refs:
            purchases |= self.create_purchase(ref, self.product_service)
        self.assertEqual(purchases[0].order_line.taxes_id[0], tax)
        wizard = self.env['purchase.order.invoice_refs'].create({
            'partner_id': self.partner.id,
            'references': '\n'.join(refs),
            'method': 'all',
            'join_purchases': True,
        })
        wizard.action_find()
        self.assertEqual(purchases, wizard.purchase_ids)
        action = wizard.action_invoice()
        invoice = self.env['account.move'].browse(action['res_id'])
        self.assertEqual(len(invoice), 1)
        self.assertEqual(invoice.amount_tax, 30)
        self.assertEqual(len(purchases[0].invoice_ids), 1)
        self.assertEqual(purchases[0].invoice_ids, invoice)
        self.assertEqual(len(purchases[1].invoice_ids), 1)
        self.assertEqual(purchases[1].invoice_ids, invoice)
        self.assertEqual(len(purchases[2].invoice_ids), 1)
        self.assertEqual(purchases[2].invoice_ids, invoice)

    def test_purchase_order_with_refund_invoice_purchase_method(self):
        ref = '01'
        purchase = self.env['purchase.order'].browse([])
        purchase |= self.create_purchase(ref, self.product_stock_01)
        self.assertEqual(len(purchase), 1)
        self.assertEqual(len(purchase.picking_ids), 1)
        picking = purchase.picking_ids
        picking.action_confirm()
        picking.action_assign()
        for move in picking.move_ids:
            move.quantity_done = move.product_uom_qty
        picking.button_validate()
        wizard = self.env['purchase.order.invoice_refs'].create({
            'partner_id': self.partner.id,
            'references': ref,
            'method': 'all',
            'join_purchases': True,
        })
        self.assertEqual(wizard.partner_id, self.partner)
        wizard.find_purchases()
        self.assertEqual(purchase, wizard.purchase_ids)
        self.assertEqual(len(wizard.line_ids), 0)
        wizard.action_invoice()
        self.assertEqual(len(purchase.invoice_ids), 1)
        invoice = purchase.invoice_ids
        invoice.invoice_date = fields.Date.today()
        invoice.action_post()
        self.assertEqual(invoice.move_type, 'in_invoice')
        wizard_refund = self.env['account.move.reversal'].with_context({
            'active_ids': invoice.ids,
            'active_model': 'account.move',
        }).create({
            'refund_method': 'refund',
            'reason': 'Refun reason',
            'journal_id': invoice.journal_id.id,
        })
        wizard_refund.reverse_moves()
        self.assertEqual(len(purchase.invoice_ids), 2)
        invoice_refund = purchase.invoice_ids - invoice
        self.assertEqual(len(invoice_refund), 1)
        self.assertEqual(invoice_refund.move_type, 'in_refund')
        wizard = self.env['purchase.order.invoice_refs'].create({
            'partner_id': self.partner.id,
            'references': ref,
            'method': 'all',
            'join_purchases': True,
        })
        self.assertEqual(wizard.partner_id, self.partner)
        wizard.find_purchases()
        self.assertEqual(purchase, wizard.purchase_ids)
        self.assertEqual(len(wizard.line_ids), 0)
        wizard.action_invoice()
        self.assertEqual(len(purchase.invoice_ids), 3)
        new_invoice = purchase.invoice_ids - invoice - invoice_refund
        self.assertEqual(len(new_invoice), 1)
        self.assertEqual(new_invoice.move_type, 'in_invoice')

    def test_purchase_order_with_refund_invoice_purchase_method_receive(self):
        ref = '01'
        purchase = self.env['purchase.order'].browse([])
        purchase |= self.create_purchase(ref, self.product_stock_02)
        self.assertEqual(len(purchase), 1)
        self.assertEqual(len(purchase.picking_ids), 1)
        picking = purchase.picking_ids
        picking.action_confirm()
        picking.action_assign()
        for move in picking.move_ids:
            move.quantity_done = move.product_uom_qty
        picking.button_validate()
        wizard = self.env['purchase.order.invoice_refs'].create({
            'partner_id': self.partner.id,
            'references': ref,
            'method': 'all',
            'join_purchases': True,
        })
        self.assertEqual(wizard.partner_id, self.partner)
        wizard.find_purchases()
        self.assertEqual(purchase, wizard.purchase_ids)
        self.assertEqual(len(wizard.line_ids), 0)
        wizard.action_invoice()
        self.assertEqual(len(purchase.invoice_ids), 1)
        invoice = purchase.invoice_ids
        self.assertFalse(invoice.invoice_date)
        invoice.invoice_date = fields.Date.today()
        self.assertTrue(invoice.invoice_date)
        invoice.action_post()
        self.assertEqual(invoice.move_type, 'in_invoice')
        wizard_refund = self.env['account.move.reversal'].with_context({
            'active_ids': invoice.ids,
            'active_model': 'account.move',
        }).create({
            'refund_method': 'refund',
            'reason': 'Refund reason',
            'journal_id': invoice.journal_id.id,
        })
        wizard_refund.reverse_moves()
        self.assertEqual(len(purchase.invoice_ids), 2)
        invoice_refund = purchase.invoice_ids - invoice
        self.assertEqual(len(invoice_refund), 1)
        self.assertEqual(invoice_refund.move_type, 'in_refund')
        wizard = self.env['purchase.order.invoice_refs'].create({
            'partner_id': self.partner.id,
            'references': ref,
            'method': 'all',
            'join_purchases': True,
        })
        self.assertEqual(wizard.partner_id, self.partner)
        wizard.find_purchases()
        self.assertEqual(purchase, wizard.purchase_ids)
        self.assertEqual(len(wizard.line_ids), 0)
        wizard.action_invoice()
        self.assertEqual(len(purchase.invoice_ids), 3)
        new_invoice = purchase.invoice_ids - invoice - invoice_refund
        self.assertEqual(len(new_invoice), 1)
        self.assertEqual(new_invoice.move_type, 'in_invoice')
