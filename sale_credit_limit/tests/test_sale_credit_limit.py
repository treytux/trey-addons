# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import _
from openerp.tests import common
from openerp.exceptions import Warning as UserError
from datetime import date


class SaleCreditLimit(common.TransactionCase):

    def setUp(self):
        super(SaleCreditLimit, self).setUp()
        self.account_obj = self.env['account.account']
        self.journal_obj = self.env['account.journal']
        self.order_line_obj = self.env['sale.order.line']
        self.order_obj = self.env['sale.order']
        self.partner_obj = self.env['res.partner']
        self.product_obj = self.env['product.product']
        self.sale_advance_obj = self.env['sale.advance.payment.inv']
        self.user_obj = self.env['res.users']
        self.partner_user_01 = self.partner_obj.create({
            'name': 'User 01',
            'email': 'user_01@test.com',
        })
        self.user_allow = self.user_obj.create({
            'partner_id': self.partner_user_01.id,
            'company_id': self.ref('base.main_company'),
            'name': 'User 01',
            'login': 'user_01',
            'password': 'user_01',
            'groups_id': [(6, 0, [
                self.ref('base.group_user'),
                self.ref('base.group_partner_manager'),
                self.ref('base.group_sale_manager'),
                self.ref(
                    'sale_credit_limit.group_view_allow_sell_credit_limit')
            ])],
        })
        self.partner_user_02 = self.partner_obj.create({
            'name': 'User 02',
            'email': 'user_02@test.com',
        })
        self.user_not_allow = self.user_obj.create({
            'partner_id': self.partner_user_02.id,
            'company_id': self.ref('base.main_company'),
            'name': 'User 02',
            'login': 'user_02',
            'password': 'user_02',
            'groups_id': [(6, 0, [
                self.ref('base.group_user'),
                self.ref('base.group_partner_manager'),
                self.ref('base.group_sale_manager'),
            ])],
        })
        self.partner_01 = self.partner_obj.create({
            'name': 'Customer 01',
            'is_company': True,
            'customer': True,
            'credit_limit': 20,
        })
        self.partner_02 = self.partner_obj.create({
            'name': 'Customer 02',
            'is_company': True,
            'customer': True,
            'credit_limit': 0,
        })
        self.product_01 = self.product_obj.create({
            'name': 'Test product 01',
            'type': 'product',
            'list_price': 10.50,
        })
        date_start = date.today().replace(day=1, month=1).strftime('%Y-%m-%d')
        self.period_id = self.env['account.fiscalyear'].search(
            [('date_start', '=', date_start)]).period_ids[8]
        self.journal_id = self.journal_obj.create({
            'name': 'Bank journal test',
            'code': 'BJT',
            'type': 'bank',
            'sequence_id': self.ref('account.sequence_bank_journal'),
            'user_id': self.ref('base.user_root'),
        })
        self.account_id = self.account_obj.create({
            'name': 'Cash test',
            'code': 'TESTX11005',
            'type': 'liquidity',
            'user_type': self.ref('account.data_account_type_asset'),
        })

    def create_invoices_open(self, order):
        context = {
            'active_model': 'sale.order',
            'active_ids': [order.id],
            'active_id': order.id,
        }
        wizard_invoice_id = self.sale_advance_obj.with_context(
            context).create({
                'advance_payment_method': 'all',
            })
        wizard_invoice_id.with_context(context).create_invoices()
        for invoice_id in order.invoice_ids:
            invoice_id.sudo().signal_workflow('invoice_open')
            self.assertEqual(invoice_id.state, 'open')
        return order.invoice_ids

    def pay_invoices(self, invoices):
        for invoice in invoices:
            invoice.sudo().pay_and_reconcile(
                invoice.amount_total, self.account_id.id,
                self.period_id.id, self.journal_id.id, self.account_id.id,
                self.period_id.id, self.journal_id.id,
                name='Payment for Invoice')
            self.assertEqual(invoice.state, 'paid')

    def test_sale_without_permission_blocking(self):
        self.user_not_allow.company_id.credit_limit_type = 'blocking'
        self.assertEqual(
            self.user_not_allow.company_id.credit_limit_type, 'blocking')
        order_01 = self.order_obj.sudo(self.user_not_allow.id).create({
            'partner_id': self.partner_01.id,
        })
        res = order_01.onchange_partner_id(order_01.partner_id.id)
        self.assertNotIn('warning', res)
        order_line = self.order_line_obj.sudo(self.user_not_allow.id).create({
            'order_id': order_01.id,
            'product_id': self.product_01.id,
            'product_uom_qty': 1,
        })
        self.assertEqual(order_line.price_unit, 10.50)
        self.assertIn('9.50', order_01.info_credit_note)
        self.assertEqual(order_01.warn_credit_note, '')
        order_01.sudo(self.user_not_allow.id).action_button_confirm()
        self.assertNotEqual(order_01.state, 'draft')
        order_02 = self.order_obj.sudo(self.user_not_allow.id).create({
            'partner_id': self.partner_01.id,
        })
        res = order_02.onchange_partner_id(order_02.partner_id.id)
        self.assertNotIn('warning', res)
        order_line = self.order_line_obj.sudo(self.user_not_allow.id).create({
            'order_id': order_02.id,
            'product_id': self.product_01.id,
            'product_uom_qty': 2,
        })
        self.assertEqual(order_line.price_unit, 10.50)
        self.assertIn('-1', order_02.info_credit_note)
        self.assertIn(_(
            'Partner \'Customer 01\' has exceeded the credit limit'),
            order_02.warn_credit_note)
        self.assertIn(_(
            'are not authorized to confirm the order'),
            order_02.warn_credit_note)
        self.assertRaises(
            UserError,
            order_02.sudo(self.user_not_allow.id).action_button_confirm)

    def test_sale_without_permission_warning(self):
        self.user_not_allow.company_id.credit_limit_type = 'warning'
        self.assertEqual(
            self.user_not_allow.company_id.credit_limit_type, 'warning')
        order_01 = self.order_obj.sudo(self.user_not_allow.id).create({
            'partner_id': self.partner_01.id,
        })
        res = order_01.onchange_partner_id(order_01.partner_id.id)
        self.assertNotIn('warning', res)
        order_line = self.order_line_obj.sudo(self.user_not_allow.id).create({
            'order_id': order_01.id,
            'product_id': self.product_01.id,
            'product_uom_qty': 1,
        })
        self.assertEqual(order_line.price_unit, 10.50)
        self.assertIn('9.50', order_01.info_credit_note)
        self.assertEqual(order_01.warn_credit_note, '')
        order_01.sudo(self.user_not_allow.id).action_button_confirm()
        self.assertNotEqual(order_01.state, 'draft')
        order_02 = self.order_obj.sudo(self.user_not_allow.id).create({
            'partner_id': self.partner_01.id,
        })
        res = order_02.onchange_partner_id(order_02.partner_id.id)
        self.assertNotIn('warning', res)
        order_line = self.order_line_obj.sudo(self.user_not_allow.id).create({
            'order_id': order_02.id,
            'product_id': self.product_01.id,
            'product_uom_qty': 2,
        })
        self.assertEqual(order_line.price_unit, 10.50)
        self.assertIn('-1', order_02.info_credit_note)
        self.assertIn(_(
            'Partner \'Customer 01\' has exceeded the credit limit'),
            order_02.warn_credit_note)
        self.assertNotIn(_(
            'are not authorized to confirm the order'),
            order_02.warn_credit_note)
        order_02.sudo(self.user_not_allow.id).action_button_confirm()
        self.assertNotEqual(order_02.state, 'draft')

    def test_sale_with_permission_blocking(self):
        self.user_allow.company_id.credit_limit_type = 'blocking'
        self.assertEqual(
            self.user_allow.company_id.credit_limit_type, 'blocking')
        order_01 = self.order_obj.sudo(self.user_allow.id).create({
            'partner_id': self.partner_01.id,
        })
        res = order_01.onchange_partner_id(order_01.partner_id.id)
        self.assertNotIn('warning', res)
        order_line = self.order_line_obj.sudo(self.user_allow.id).create({
            'order_id': order_01.id,
            'product_id': self.product_01.id,
            'product_uom_qty': 1,
        })
        self.assertEqual(order_line.price_unit, 10.50)
        self.assertIn('9.50', order_01.info_credit_note)
        self.assertEqual(order_01.warn_credit_note, '')
        order_01.sudo(self.user_allow.id).action_button_confirm()
        self.assertNotEqual(order_01.state, 'draft')
        order_02 = self.order_obj.sudo(self.user_allow.id).create({
            'partner_id': self.partner_01.id,
        })
        res = order_02.onchange_partner_id(order_02.partner_id.id)
        self.assertNotIn('warning', res)
        order_line = self.order_line_obj.sudo(self.user_allow.id).create({
            'order_id': order_02.id,
            'product_id': self.product_01.id,
            'product_uom_qty': 2,
        })
        self.assertEqual(order_line.price_unit, 10.50)
        self.assertIn('-1', order_02.info_credit_note)
        self.assertIn(_(
            'Partner \'Customer 01\' has exceeded the credit limit'),
            order_02.warn_credit_note)
        self.assertNotIn(_(
            'are not authorized to confirm the order'),
            order_02.warn_credit_note)
        order_02.sudo(self.user_allow.id).action_button_confirm()
        self.assertNotEqual(order_02.state, 'draft')
        self.assertIn('-1', order_02.info_credit_note)
        self.assertIn(_(
            'Partner \'Customer 01\' has exceeded the credit limit'),
            order_02.warn_credit_note)
        self.assertNotIn(_(
            'are not authorized to confirm the order'),
            order_02.warn_credit_note)

    def test_sale_with_permission_warning(self):
        self.user_allow.company_id.credit_limit_type = 'warning'
        self.assertEqual(
            self.user_allow.company_id.credit_limit_type, 'warning')
        order_01 = self.order_obj.sudo(self.user_allow.id).create({
            'partner_id': self.partner_01.id,
        })
        res = order_01.onchange_partner_id(order_01.partner_id.id)
        self.assertNotIn('warning', res)
        order_line = self.order_line_obj.sudo(self.user_allow.id).create({
            'order_id': order_01.id,
            'product_id': self.product_01.id,
            'product_uom_qty': 1,
        })
        self.assertEqual(order_line.price_unit, 10.50)
        self.assertIn('9.50', order_01.info_credit_note)
        self.assertEqual(order_01.warn_credit_note, '')
        order_01.sudo(self.user_allow.id).action_button_confirm()
        self.assertNotEqual(order_01.state, 'draft')
        order_02 = self.order_obj.sudo(self.user_allow.id).create({
            'partner_id': self.partner_01.id,
        })
        res = order_02.onchange_partner_id(order_02.partner_id.id)
        self.assertNotIn('warning', res)
        order_line = self.order_line_obj.sudo(self.user_allow.id).create({
            'order_id': order_02.id,
            'product_id': self.product_01.id,
            'product_uom_qty': 2,
        })
        self.assertEqual(order_line.price_unit, 10.50)
        self.assertIn('-1', order_02.info_credit_note)
        self.assertIn(_(
            'Partner \'Customer 01\' has exceeded the credit limit'),
            order_02.warn_credit_note)
        self.assertNotIn(_(
            'are not authorized to confirm the order'),
            order_02.warn_credit_note)
        order_02.sudo(self.user_allow.id).action_button_confirm()
        self.assertNotEqual(order_02.state, 'draft')
        self.assertIn('-1', order_02.info_credit_note)
        self.assertIn(_(
            'Partner \'Customer 01\' has exceeded the credit limit'),
            order_02.warn_credit_note)
        self.assertNotIn(_(
            'are not authorized to confirm the order'),
            order_02.warn_credit_note)

    def test_invoice_without_permission_blocking_01(self):
        self.user_not_allow.company_id.credit_limit_type = 'blocking'
        self.assertEqual(
            self.user_not_allow.company_id.credit_limit_type, 'blocking')
        order_01 = self.order_obj.sudo(self.user_not_allow.id).create({
            'partner_id': self.partner_01.id,
            'order_policy': 'manual',
        })
        res = order_01.onchange_partner_id(order_01.partner_id.id)
        self.assertNotIn('warning', res)
        order_line = self.order_line_obj.sudo(self.user_not_allow.id).create({
            'order_id': order_01.id,
            'product_id': self.product_01.id,
            'product_uom_qty': 1,
        })
        self.assertEqual(order_line.price_unit, 10.50)
        self.assertIn('9.50', order_01.info_credit_note)
        self.assertEqual(order_01.warn_credit_note, '')
        order_01.sudo(self.user_not_allow.id).action_button_confirm()
        self.assertNotEqual(order_01.state, 'draft')
        self.create_invoices_open(order_01)
        order_02 = self.order_obj.sudo(self.user_not_allow.id).create({
            'partner_id': self.partner_01.id,
        })
        res = order_02.onchange_partner_id(order_02.partner_id.id)
        self.assertNotIn('warning', res)
        order_line = self.order_line_obj.sudo(self.user_not_allow.id).create({
            'order_id': order_02.id,
            'product_id': self.product_01.id,
            'product_uom_qty': 1,
        })
        self.assertEqual(order_line.price_unit, 10.50)
        self.assertIn('-1', order_02.info_credit_note)
        self.assertIn(_(
            'Partner \'Customer 01\' has exceeded the credit limit'),
            order_02.warn_credit_note)
        self.assertIn(_(
            'are not authorized to confirm the order'),
            order_02.warn_credit_note)
        self.assertRaises(
            UserError,
            order_02.sudo(self.user_not_allow.id).action_button_confirm)

    def test_invoice_without_permission_warning_01(self):
        self.user_not_allow.company_id.credit_limit_type = 'warning'
        self.assertEqual(
            self.user_not_allow.company_id.credit_limit_type, 'warning')
        order_01 = self.order_obj.sudo(self.user_not_allow.id).create({
            'partner_id': self.partner_01.id,
            'order_policy': 'manual',
        })
        res = order_01.onchange_partner_id(order_01.partner_id.id)
        self.assertNotIn('warning', res)
        order_line = self.order_line_obj.sudo(self.user_not_allow.id).create({
            'order_id': order_01.id,
            'product_id': self.product_01.id,
            'product_uom_qty': 1,
        })
        self.assertEqual(order_line.price_unit, 10.50)
        self.assertIn('9.50', order_01.info_credit_note)
        self.assertEqual(order_01.warn_credit_note, '')
        order_01.sudo(self.user_not_allow.id).action_button_confirm()
        self.assertNotEqual(order_01.state, 'draft')
        self.create_invoices_open(order_01)
        order_02 = self.order_obj.sudo(self.user_not_allow.id).create({
            'partner_id': self.partner_01.id,
        })
        res = order_02.onchange_partner_id(order_02.partner_id.id)
        self.assertNotIn('warning', res)
        order_line = self.order_line_obj.sudo(self.user_not_allow.id).create({
            'order_id': order_02.id,
            'product_id': self.product_01.id,
            'product_uom_qty': 1,
        })
        self.assertEqual(order_line.price_unit, 10.50)
        self.assertIn('-1', order_02.info_credit_note)
        self.assertIn(_(
            'Partner \'Customer 01\' has exceeded the credit limit'),
            order_02.warn_credit_note)
        order_02.sudo(self.user_not_allow.id).action_button_confirm()
        self.assertNotEqual(order_02.state, 'draft')

    def test_invoice_without_permission_blocking_02(self):
        self.user_not_allow.company_id.credit_limit_type = 'blocking'
        self.assertEqual(
            self.user_not_allow.company_id.credit_limit_type, 'blocking')
        order_01 = self.order_obj.sudo(self.user_not_allow.id).create({
            'partner_id': self.partner_01.id,
            'order_policy': 'manual',
        })
        res = order_01.onchange_partner_id(order_01.partner_id.id)
        self.assertNotIn('warning', res)
        order_line = self.order_line_obj.sudo(self.user_not_allow.id).create({
            'order_id': order_01.id,
            'product_id': self.product_01.id,
            'product_uom_qty': 1,
        })
        self.assertEqual(order_line.price_unit, 10.50)
        self.assertIn('9.50', order_01.info_credit_note)
        self.assertEqual(order_01.warn_credit_note, '')
        order_01.sudo(self.user_not_allow.id).action_button_confirm()
        self.assertNotEqual(order_01.state, 'draft')
        invoices = self.create_invoices_open(order_01)
        self.pay_invoices(invoices)
        self.assertTrue(order_01.invoiced)
        order_02 = self.order_obj.sudo(self.user_not_allow.id).create({
            'partner_id': self.partner_01.id,
        })
        res = order_02.onchange_partner_id(order_02.partner_id.id)
        self.assertNotIn('warning', res)
        order_line = self.order_line_obj.sudo(self.user_not_allow.id).create({
            'order_id': order_02.id,
            'product_id': self.product_01.id,
            'product_uom_qty': 1,
        })
        self.assertEqual(order_line.price_unit, 10.50)
        self.assertIn('9.50', order_02.info_credit_note)
        self.assertEqual(order_02.warn_credit_note, '')
        order_02.sudo(self.user_not_allow.id).action_button_confirm()
        self.assertNotEqual(order_02.state, 'draft')
        self.assertIn('9.50', order_02.info_credit_note)
        self.assertEqual(order_02.warn_credit_note, '')
        order_03 = self.order_obj.sudo(self.user_not_allow.id).create({
            'partner_id': self.partner_01.id,
        })
        res = order_03.onchange_partner_id(order_03.partner_id.id)
        self.assertNotIn('warning', res)
        order_line = self.order_line_obj.sudo(self.user_not_allow.id).create({
            'order_id': order_03.id,
            'product_id': self.product_01.id,
            'product_uom_qty': 2,
        })
        self.assertEqual(order_line.price_unit, 10.50)
        self.assertIn('-1', order_03.info_credit_note)
        self.assertIn(_(
            'Partner \'Customer 01\' has exceeded the credit limit'),
            order_03.warn_credit_note)
        self.assertIn(_(
            'are not authorized to confirm the order'),
            order_03.warn_credit_note)
        self.assertRaises(
            UserError,
            order_03.sudo(self.user_not_allow.id).action_button_confirm)

    def test_invoice_without_permission_warning_02(self):
        self.user_not_allow.company_id.credit_limit_type = 'warning'
        self.assertEqual(
            self.user_not_allow.company_id.credit_limit_type, 'warning')
        order_01 = self.order_obj.sudo(self.user_not_allow.id).create({
            'partner_id': self.partner_01.id,
            'order_policy': 'manual',
        })
        res = order_01.onchange_partner_id(order_01.partner_id.id)
        self.assertNotIn('warning', res)
        order_line = self.order_line_obj.sudo(self.user_not_allow.id).create({
            'order_id': order_01.id,
            'product_id': self.product_01.id,
            'product_uom_qty': 1,
        })
        self.assertEqual(order_line.price_unit, 10.50)
        self.assertIn('9.50', order_01.info_credit_note)
        self.assertEqual(order_01.warn_credit_note, '')
        order_01.sudo(self.user_not_allow.id).action_button_confirm()
        self.assertNotEqual(order_01.state, 'draft')
        invoices = self.create_invoices_open(order_01)
        self.pay_invoices(invoices)
        self.assertTrue(order_01.invoiced)
        order_02 = self.order_obj.sudo(self.user_not_allow.id).create({
            'partner_id': self.partner_01.id,
        })
        res = order_02.onchange_partner_id(order_02.partner_id.id)
        self.assertNotIn('warning', res)
        order_line = self.order_line_obj.sudo(self.user_not_allow.id).create({
            'order_id': order_02.id,
            'product_id': self.product_01.id,
            'product_uom_qty': 1,
        })
        self.assertEqual(order_line.price_unit, 10.50)
        self.assertIn('9.50', order_02.info_credit_note)
        self.assertEqual(order_02.warn_credit_note, '')
        order_02.sudo(self.user_not_allow.id).action_button_confirm()
        self.assertNotEqual(order_02.state, 'draft')
        self.assertIn('9.50', order_02.info_credit_note)
        self.assertEqual(order_02.warn_credit_note, '')
        order_03 = self.order_obj.sudo(self.user_not_allow.id).create({
            'partner_id': self.partner_01.id,
        })
        res = order_03.onchange_partner_id(order_03.partner_id.id)
        self.assertNotIn('warning', res)
        order_line = self.order_line_obj.sudo(self.user_not_allow.id).create({
            'order_id': order_03.id,
            'product_id': self.product_01.id,
            'product_uom_qty': 2,
        })
        self.assertEqual(order_line.price_unit, 10.50)
        self.assertIn('-1', order_03.info_credit_note)
        self.assertIn(_(
            'Partner \'Customer 01\' has exceeded the credit limit'),
            order_03.warn_credit_note)
        self.assertNotIn(_(
            'are not authorized to confirm the order'),
            order_03.warn_credit_note)
        order_03.sudo(self.user_not_allow.id).action_button_confirm()
        self.assertNotEqual(order_03.state, 'draft')

    def test_invoice_without_permission_warning_onchange(self):
        self.user_not_allow.company_id.credit_limit_type = 'warning'
        self.assertEqual(
            self.user_not_allow.company_id.credit_limit_type, 'warning')
        order_01 = self.order_obj.sudo(self.user_not_allow.id).create({
            'partner_id': self.partner_01.id,
            'order_policy': 'manual',
        })
        res = order_01.onchange_partner_id(order_01.partner_id.id)
        self.assertNotIn('warning', res)
        order_line = self.order_line_obj.sudo(self.user_not_allow.id).create({
            'order_id': order_01.id,
            'product_id': self.product_01.id,
            'product_uom_qty': 1,
        })
        self.assertEqual(order_line.price_unit, 10.50)
        self.assertIn('9.50', order_01.info_credit_note)
        self.assertEqual(order_01.warn_credit_note, '')
        order_01.sudo(self.user_not_allow.id).action_button_confirm()
        self.assertNotEqual(order_01.state, 'draft')
        self.create_invoices_open(order_01)
        order_02 = self.order_obj.sudo(self.user_not_allow.id).create({
            'partner_id': self.partner_01.id,
        })
        res = order_02.onchange_partner_id(order_02.partner_id.id)
        self.assertNotIn('warning', res)
        order_line = self.order_line_obj.sudo(self.user_not_allow.id).create({
            'order_id': order_02.id,
            'product_id': self.product_01.id,
            'product_uom_qty': 1,
        })
        self.assertEqual(order_line.price_unit, 10.50)
        self.assertIn('-1', order_02.info_credit_note)
        self.assertIn(_(
            'Partner \'Customer 01\' has exceeded the credit limit'),
            order_02.warn_credit_note)
        self.assertNotIn(_(
            'are not authorized to confirm the order'),
            order_02.warn_credit_note)
        order_02.sudo(self.user_not_allow.id).action_button_confirm()
        self.create_invoices_open(order_02)
        sales = self.env['sale.order'].search([
            ('partner_id', '=', self.partner_01.id),
            ('state', '!=', 'draft'),
        ])
        self.assertEqual(len(sales), 2)
        order_03 = self.order_obj.sudo(self.user_not_allow.id).create({
            'partner_id': self.partner_01.id,
        })
        res = order_03.onchange_partner_id(order_03.partner_id.id)
        self.assertIn('warning', res)
        self.assertIn(_(
            'Partner \'Customer 01\' has exceeded the credit limit'),
            order_02.warn_credit_note)
        self.assertNotIn(_(
            'are not authorized to confirm the order'),
            order_02.warn_credit_note)

    def test_sale_without_permission_blocking_no_credit_limit(self):
        self.user_not_allow.company_id.credit_limit_type = 'blocking'
        self.assertEqual(
            self.user_not_allow.company_id.credit_limit_type, 'blocking')
        order_01 = self.order_obj.sudo(self.user_not_allow.id).create({
            'partner_id': self.partner_02.id,
        })
        res = order_01.onchange_partner_id(order_01.partner_id.id)
        self.assertNotIn('warning', res)
        order_line = self.order_line_obj.sudo(self.user_not_allow.id).create({
            'order_id': order_01.id,
            'product_id': self.product_01.id,
            'product_uom_qty': 1,
        })
        self.assertEqual(order_line.price_unit, 10.50)
        self.assertEqual(order_01.info_credit_note, '')
        self.assertEqual(order_01.warn_credit_note, '')
        order_01.sudo(self.user_not_allow.id).action_button_confirm()
        self.assertNotEqual(order_01.state, 'draft')
        order_02 = self.order_obj.sudo(self.user_not_allow.id).create({
            'partner_id': self.partner_02.id,
        })
        res = order_02.onchange_partner_id(order_02.partner_id.id)
        self.assertNotIn('warning', res)
        order_line = self.order_line_obj.sudo(self.user_not_allow.id).create({
            'order_id': order_02.id,
            'product_id': self.product_01.id,
            'product_uom_qty': 2,
        })
        self.assertEqual(order_line.price_unit, 10.50)
        self.assertEqual(order_02.info_credit_note, '')
        self.assertEqual(order_02.warn_credit_note, '')
        order_02.sudo(self.user_not_allow.id).action_button_confirm()
        self.assertEqual(order_02.info_credit_note, '')
        self.assertEqual(order_02.warn_credit_note, '')

    def test_sale_without_permission_warning_no_credit_limit(self):
        self.user_not_allow.company_id.credit_limit_type = 'warning'
        self.assertEqual(
            self.user_not_allow.company_id.credit_limit_type, 'warning')
        order_01 = self.order_obj.sudo(self.user_not_allow.id).create({
            'partner_id': self.partner_02.id,
        })
        res = order_01.onchange_partner_id(order_01.partner_id.id)
        self.assertNotIn('warning', res)
        order_line = self.order_line_obj.sudo(self.user_not_allow.id).create({
            'order_id': order_01.id,
            'product_id': self.product_01.id,
            'product_uom_qty': 1,
        })
        self.assertEqual(order_line.price_unit, 10.50)
        self.assertEqual(order_01.info_credit_note, '')
        self.assertEqual(order_01.warn_credit_note, '')
        order_01.sudo(self.user_not_allow.id).action_button_confirm()
        self.assertNotEqual(order_01.state, 'draft')
        order_02 = self.order_obj.sudo(self.user_not_allow.id).create({
            'partner_id': self.partner_02.id,
        })
        res = order_02.onchange_partner_id(order_02.partner_id.id)
        self.assertNotIn('warning', res)
        order_line = self.order_line_obj.sudo(self.user_not_allow.id).create({
            'order_id': order_02.id,
            'product_id': self.product_01.id,
            'product_uom_qty': 2,
        })
        self.assertEqual(order_line.price_unit, 10.50)
        self.assertEqual(order_02.info_credit_note, '')
        self.assertEqual(order_02.warn_credit_note, '')
        order_02.sudo(self.user_not_allow.id).action_button_confirm()
        self.assertEqual(order_02.info_credit_note, '')
        self.assertEqual(order_02.warn_credit_note, '')
