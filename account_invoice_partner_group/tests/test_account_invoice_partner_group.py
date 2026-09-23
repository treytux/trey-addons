###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests import common


class TestAccountInvoicePartnerGroup(common.TransactionCase):

    def setUp(self):
        super().setUp()
        self.partner_1 = self.env['res.partner'].create({
            'name': 'Test partner 1',
            'is_company': True,
        })
        self.partner_2 = self.env['res.partner'].create({
            'name': 'Test partner 2',
            'is_company': True,
        })
        self.type_revenue = self.env.ref('account.data_account_type_revenue')
        self.account_type_regular = self.env["account.account.type"].create({
            'name': 'Test Regular',
            'type': 'other',
        })
        self.account_income = self.env["account.account"].create({
            'name': 'Test Income',
            'code': 'TEST_IN',
            'user_type_id': self.account_type_regular.id,
            'reconcile': False,
        })
        self.account_sale = self.env['account.account'].create({
            'name': 'Sale',
            'code': 'XX_700',
            'user_type_id': self.type_revenue.id,
            'reconcile': True,
        })
        self.journal = self.env['account.journal'].create({
            'name': 'Test journal for sale',
            'type': 'sale',
            'code': 'TSALE',
            'default_debit_account_id': self.account_sale.id,
            'default_credit_account_id': self.account_sale.id,
        })
        self.product = self.env['product.product'].create({
            'type': 'consu',
            'company_id': False,
            'name': 'Test product',
            'standard_price': 10,
            'list_price': 60,
        })
        self.partner_group_1 = self.env['res.partner'].create({
            'name': 'Test partner group 1',
            'is_company': False,
        })
        self.partner_group_2 = self.env['res.partner'].create({
            'name': 'Test partner group 2',
            'is_company': False,
        })
        self.partner_1.partner_group_id = self.partner_group_1.id

    def create_sale(self, partner):
        sale = self.env['sale.order'].create({
            'partner_id': partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product.id,
                    'price_unit': 20,
                    'product_uom_qty': 1,
                }),
            ]
        })
        sale.onchange_partner_id()
        return sale

    def picking_done(self, picking):
        picking.action_confirm()
        picking.action_assign()
        for move in picking.move_lines:
            move.quantity_done = move.product_uom_qty
        picking.action_done()

    def get_ctx(self, sale):
        return {
            'tracking_disable': True,
            'mail_notrack': True,
            'mail_create_nolog': True,
            'active_model': 'sale.order',
            'active_ids': sale.ids,
            'active_id': sale.id,
        }

    def test_sale_order_partner_group_invoice(self):
        self.assertEqual(self.partner_1.partner_group_id, self.partner_group_1)
        sale = self.create_sale(self.partner_1)
        self.assertEqual(sale.partner_group_id, self.partner_1.partner_group_id)
        self.assertEqual(sale.state, 'draft')
        sale.action_confirm()
        self.assertEqual(sale.state, 'sale')
        self.assertEqual(len(sale.invoice_ids), 0)
        sale.action_invoice_create()
        self.assertEqual(len(sale.invoice_ids), 1)
        invoice = sale.invoice_ids[0]
        self.assertEqual(sale.partner_group_id, invoice.partner_group_id)

    def test_sale_order_partner_group_wizard_advance_invoice_01(self):
        self.assertEqual(self.partner_1.partner_group_id, self.partner_group_1)
        sale = self.create_sale(self.partner_1)
        self.assertEqual(sale.partner_group_id, self.partner_1.partner_group_id)
        self.assertEqual(sale.state, 'draft')
        sale.action_confirm()
        self.assertEqual(sale.state, 'sale')
        self.assertEqual(len(sale.invoice_ids), 0)
        ctx = self.get_ctx(sale)
        wizard = self.env['sale.advance.payment.inv'].with_context(ctx).create({
            'advance_payment_method': 'all',
        })
        wizard.create_invoices()
        self.assertEqual(len(sale.invoice_ids), 1)
        invoice = sale.invoice_ids[0]
        self.assertEqual(sale.partner_group_id, invoice.partner_group_id)

    def test_sale_order_partner_group_wizard_advance_invoice_02(self):
        self.assertEqual(self.partner_1.partner_group_id, self.partner_group_1)
        sale = self.create_sale(self.partner_1)
        self.assertEqual(sale.partner_group_id, self.partner_1.partner_group_id)
        self.assertEqual(sale.state, 'draft')
        sale.action_confirm()
        self.assertEqual(sale.state, 'sale')
        self.assertEqual(len(sale.invoice_ids), 0)
        ctx = self.get_ctx(sale)
        wizard = self.env['sale.advance.payment.inv'].with_context(ctx).create({
            'advance_payment_method': 'percentage',
            'amount': 50.0,
        })
        wizard.create_invoices()
        self.assertEqual(len(sale.invoice_ids), 1)
        invoice = sale.invoice_ids[0]
        self.assertEqual(sale.partner_group_id, invoice.partner_group_id)

    def test_sale_order_partner_group_wizard_advance_invoice_03(self):
        self.assertEqual(self.partner_1.partner_group_id, self.partner_group_1)
        sale = self.create_sale(self.partner_1)
        self.assertEqual(sale.partner_group_id, self.partner_1.partner_group_id)
        self.assertEqual(sale.state, 'draft')
        sale.action_confirm()
        self.assertEqual(sale.state, 'sale')
        self.assertEqual(len(sale.invoice_ids), 0)
        ctx = self.get_ctx(sale)
        wizard = self.env['sale.advance.payment.inv'].with_context(ctx).create({
            'advance_payment_method': 'fixed',
            'amount': 100,
            'deposit_account_id': self.account_income.id,
        })
        wizard.create_invoices()
        self.assertEqual(len(sale.invoice_ids), 1)
        invoice = sale.invoice_ids[0]
        self.assertEqual(sale.partner_group_id, invoice.partner_group_id)

    def test_sale_order_partner_group_wizard_advance_invoice_04(self):
        self.assertEqual(self.partner_1.partner_group_id, self.partner_group_1)
        sale = self.create_sale(self.partner_1)
        self.assertEqual(sale.partner_group_id, self.partner_1.partner_group_id)
        self.assertEqual(sale.state, 'draft')
        sale.action_confirm()
        self.assertEqual(sale.state, 'sale')
        self.assertEqual(len(sale.picking_ids), 1)
        self.picking_done(sale.picking_ids[0])
        self.assertEqual(sale.picking_ids[0].state, 'done')
        self.assertEqual(len(sale.invoice_ids), 0)
        ctx = self.get_ctx(sale)
        wizard = self.env['sale.advance.payment.inv'].with_context(ctx).create({
            'advance_payment_method': 'delivered',
        })
        wizard.create_invoices()
        self.assertEqual(len(sale.invoice_ids), 1)
        invoice = sale.invoice_ids[0]
        self.assertEqual(sale.partner_group_id, invoice.partner_group_id)

    def test_sale_return_partner_group_invoice(self):
        sale_return = self.env['sale.order'].create({
            'is_return': True,
            'partner_id': self.partner_1.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product.id,
                    'product_uom_qty': 1,
                }),
            ],
        })
        sale_return.onchange_partner_id()
        self.assertEqual(
            sale_return.partner_group_id, self.partner_1.partner_group_id)
        sale_return.action_confirm()
        self.assertEqual(sale_return.state, 'sale')
        self.picking_done(sale_return.picking_ids[0])
        self.assertEqual(len(sale_return.invoice_ids), 0)
        sale_return.action_invoice_create()
        self.assertEqual(len(sale_return.invoice_ids), 1)
        invoice_return = sale_return.invoice_ids[0]
        self.assertEqual(
            sale_return.partner_group_id, invoice_return.partner_group_id)

    def test_sale_return_partner_group_invoice_wizard_advance(self):
        sale_return = self.env['sale.order'].create({
            'is_return': True,
            'partner_id': self.partner_1.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product.id,
                    'product_uom_qty': 1,
                }),
            ],
        })
        sale_return.onchange_partner_id()
        self.assertEqual(
            sale_return.partner_group_id, self.partner_1.partner_group_id)
        sale_return.action_confirm()
        self.assertEqual(sale_return.state, 'sale')
        self.picking_done(sale_return.picking_ids[0])
        self.assertEqual(len(sale_return.invoice_ids), 0)
        ctx = self.get_ctx(sale_return)
        wizard = self.env['sale.advance.payment.inv'].with_context(ctx).create({
            'advance_payment_method': 'all',
        })
        wizard.create_invoices()
        self.assertEqual(len(sale_return.invoice_ids), 1)
        invoice_return = sale_return.invoice_ids[0]
        self.assertEqual(
            sale_return.partner_group_id, invoice_return.partner_group_id)

    def test_create_invoice_partner_group(self):
        invoice = self.env['account.invoice'].create({
            'partner_id': self.partner_1.id,
            'journal_id': self.journal.id,
            'invoice_line_ids': [
                (0, 0, {
                    'product_id': self.product.id,
                    'name': self.product.name,
                    'price_unit': self.product.lst_price,
                    'account_id': self.account_sale.id,
                    'quantity': 1,
                }),
            ],
        })
        invoice._onchange_partner_id()
        self.assertEqual(
            invoice.partner_group_id, self.partner_1.partner_group_id)
        self.assertEqual(invoice.partner_group_id, self.partner_group_1)
        self.partner_2.partner_group_id = self.partner_group_2
        self.assertEqual(self.partner_2.partner_group_id, self.partner_group_2)
        invoice.partner_id = self.partner_2.id
        invoice._onchange_partner_id()
        self.assertEqual(
            invoice.partner_group_id, self.partner_2.partner_group_id)
        self.assertEqual(invoice.partner_group_id, self.partner_group_2)

    def test_sale_order_invoice_change_partner_group(self):
        self.assertEqual(self.partner_1.partner_group_id, self.partner_group_1)
        sale = self.create_sale(self.partner_1)
        self.assertEqual(sale.partner_group_id, self.partner_1.partner_group_id)
        self.assertEqual(sale.state, 'draft')
        sale.partner_group_id = self.partner_group_2
        self.assertEqual(sale.partner_group_id, self.partner_group_2)
        self.assertNotEqual(
            sale.partner_id.partner_group_id, self.partner_group_2)
        self.assertNotEqual(
            self.partner_1.partner_group_id, self.partner_group_2)
        sale.action_confirm()
        self.assertEqual(sale.state, 'sale')
        self.assertEqual(len(sale.invoice_ids), 0)
        sale.action_invoice_create()
        self.assertEqual(len(sale.invoice_ids), 1)
        invoice = sale.invoice_ids[0]
        self.assertEqual(invoice.partner_group_id, sale.partner_group_id)
        self.assertEqual(invoice.partner_group_id, self.partner_group_2)
        self.assertNotEqual(invoice.partner_group_id, self.partner_group_1)

    def test_multiple_sale_order_create_invoice(self):
        self.assertEqual(self.partner_1.partner_group_id, self.partner_group_1)
        sale_01 = self.create_sale(self.partner_1)
        self.assertEqual(
            sale_01.partner_group_id, self.partner_1.partner_group_id)
        self.assertEqual(sale_01.state, 'draft')
        self.partner_2.partner_group_id = self.partner_group_2.id
        self.assertEqual(self.partner_2.partner_group_id, self.partner_group_2)
        sale_02 = self.create_sale(self.partner_2)
        self.assertEqual(
            sale_02.partner_group_id, self.partner_2.partner_group_id)
        self.assertEqual(sale_02.state, 'draft')
        sale_01.action_confirm()
        sale_02.action_confirm()
        self.assertEqual(sale_01.state, 'sale')
        self.assertEqual(sale_02.state, 'sale')
        sales = self.env['sale.order'].browse([sale_01.id, sale_02.id])
        self.assertEqual(len(sale_01.invoice_ids), 0)
        self.assertEqual(len(sale_02.invoice_ids), 0)
        sales.action_invoice_create()
        self.assertEqual(len(sale_01.invoice_ids), 1)
        self.assertEqual(len(sale_02.invoice_ids), 1)
        invoice_01 = sale_01.invoice_ids[0]
        invoice_02 = sale_02.invoice_ids[0]
        self.assertEqual(sale_01.partner_group_id, invoice_01.partner_group_id)
        self.assertEqual(sale_02.partner_group_id, invoice_02.partner_group_id)
