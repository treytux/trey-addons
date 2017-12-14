# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp.tests import common
from openerp.exceptions import Warning as UserError
from datetime import date
import logging
_log = logging.getLogger(__name__)


class SaleCreditLimit(common.TransactionCase):

    def setUp(self):
        super(SaleCreditLimit, self).setUp()
        self.account_obj = self.env['account.account']
        self.journal_obj = self.env['account.journal']
        self.order_line_obj = self.env['sale.order.line']
        self.order_obj = self.env['sale.order']
        self.partner_obj = self.env['res.partner']
        self.product_obj = self.env['product.product']
        self.product_templ_obj = self.env['product.template']
        self.sale_advance_obj = self.env['sale.advance.payment.inv']
        self.user_obj = self.env['res.users']

        # Create partner and user belong 'Allow sell with credit limit' group
        partner_data = {
            'name': 'User 01',
            'email': 'user_01@test.com'}
        self.partner = self.partner_obj.create(partner_data)
        user_data = {
            'partner_id': self.partner.id,
            'company_id': self.ref('base.main_company'),
            'name': 'User 01',
            'login': 'user_01',
            'password': 'user_01',
            'groups_id': [(6, 0, [
                self.ref('base.group_user'),
                self.ref('base.group_partner_manager'),
                self.ref('base.group_sale_manager'),
                self.ref(
                    'sale_credit_limit.group_view_allow_sell_credit_limit'
                )])]}
        self.user_allow = self.user_obj.create(user_data)

        # Create partner and user not belong 'Allow sell with credit limit'
        # group
        partner_data = {
            'name': 'User 02',
            'email': 'user_02@test.com'}
        self.partner = self.partner_obj.create(partner_data)
        user_data = {
            'partner_id': self.partner.id,
            'company_id': self.ref('base.main_company'),
            'name': 'User 02',
            'login': 'user_02',
            'password': 'user_02',
            'groups_id': [(6, 0, [
                self.ref('base.group_user'),
                self.ref('base.group_partner_manager'),
                self.ref('base.group_sale_manager')])]}
        self.user_not_allow = self.user_obj.create(user_data)

        # Create partner
        partner_data = {
            'name': 'Customer 01',
            'is_company': True,
            'customer': True,
            'email': 'customer1@test.com',
            'street': 'Calle Real, 33',
            'phone': '666225522',
            'credit_limit': 20}
        self.partner_01 = self.partner_obj.create(partner_data)

        # Create products
        self.product_01 = self.product_obj.create({
            'name': 'Test product 01',
            'type': 'product',
            'list_price': 10.50})

        date_start = date.today().replace(day=1, month=1).strftime('%Y-%m-%d')
        self.period_id = self.env['account.fiscalyear'].search(
            [('date_start', '=', date_start)]).period_ids[8]

        # Create journal
        journal_data = {
            'name': 'Bank journal test',
            'code': 'BJT',
            'type': 'bank',
            'sequence_id': self.ref('account.sequence_bank_journal'),
            'user_id': self.ref('base.user_root')}
        self.journal_id = self.journal_obj.create(journal_data)

        # Create account
        account_data = {
            'name': 'Cash test',
            'code': 'X11005',
            'type': 'liquidity',
            'user_type': self.ref('account.data_account_type_asset')}
        self.account_id = self.account_obj.create(account_data)

    def test_sale_without_permission(self):
        # USER WITHOUT PERMISSION
        # Create first order: allow confirm because because it still has
        # limits.
        order_01 = self.order_obj.create({
            'partner_id': self.partner_01.id})
        self.order_line_obj.create({
            'order_id': order_01.id,
            'product_id': self.product_01.id,
            'product_uom_qty': 1})
        # Confirm sale order
        order_01.sudo(self.user_not_allow.id).action_button_confirm()
        # Check sale order is confirmed
        self.assertNotEqual(order_01.state, 'draft')

        # Create second order: do not allow confirm because it has no limit.
        order_02 = self.order_obj.create({
            'partner_id': self.partner_01.id})
        self.order_line_obj.create({
            'order_id': order_02.id,
            'product_id': self.product_01.id,
            'product_uom_qty': 1})
        # Confirm sale order: catch raise warning
        self.assertRaises(
            UserError,
            order_02.sudo(self.user_not_allow.id).action_button_confirm)

    def test_sale_with_permission(self):
        # USER WITH PERMISSION
        # Create first order: allow confirm because because it still has
        # limits and user has permissions.
        order_01 = self.order_obj.create({
            'partner_id': self.partner_01.id})
        self.order_line_obj.create({
            'order_id': order_01.id,
            'product_id': self.product_01.id,
            'product_uom_qty': 1})
        # Confirm sale order
        order_01.sudo(self.user_allow.id).action_button_confirm()
        # Check sale order is confirmed
        self.assertNotEqual(order_01.state, 'draft')

        # Create second order: confirms even exceeded the limit because the
        # user has permissions
        order_02 = self.order_obj.create({
            'partner_id': self.partner_01.id})
        self.order_line_obj.create({
            'order_id': order_02.id,
            'product_id': self.product_01.id,
            'product_uom_qty': 1})
        # Confirm sale order
        order_02.sudo(self.user_allow.id).action_button_confirm()
        # Check sale order is confirmed
        self.assertNotEqual(order_02.state, 'draft')

    def test_invoice_without_permission_01(self):
        # USER WITHOUT PERMISSION
        # Create first order: allow confirm because because it still has
        # limits.
        order_01 = self.order_obj.create({
            'partner_id': self.partner_01.id,
            'order_policy': 'manual'})
        self.order_line_obj.create({
            'order_id': order_01.id,
            'product_id': self.product_01.id,
            'product_uom_qty': 1})
        # Confirm sale order
        order_01.sudo(self.user_not_allow.id).action_button_confirm()
        # Check sale order is confirmed
        self.assertNotEqual(order_01.state, 'draft')

        # Create invoice
        context = {
            'active_model': 'sale.order',
            'active_ids': [order_01.id],
            'active_id': order_01.id}
        wizard_invoice_id = self.sale_advance_obj.with_context(
            context).create({
                'advance_payment_method': 'all'})
        wizard_invoice_id.with_context(context).create_invoices()
        for invoice_id in order_01.invoice_ids:
            invoice_id.signal_workflow('invoice_open')
            # Check if invoice is open
            self.assertEqual(invoice_id.state, 'open')

        # Create second order: do not allow confirm because it has no limit.
        order_02 = self.order_obj.create({
            'partner_id': self.partner_01.id})
        self.order_line_obj.create({
            'order_id': order_02.id,
            'product_id': self.product_01.id,
            'product_uom_qty': 1})
        # Confirm sale order: catch raise warning
        self.assertRaises(
            UserError,
            order_02.sudo(self.user_not_allow.id).action_button_confirm)

    def test_invoice_without_permission_02(self):
        # USER WITHOUT PERMISSION
        # Create first order: allow confirm because because it still has
        # limits.
        order_01 = self.order_obj.create({
            'partner_id': self.partner_01.id,
            'order_policy': 'manual'})
        self.order_line_obj.create({
            'order_id': order_01.id,
            'product_id': self.product_01.id,
            'product_uom_qty': 1})
        # Confirm sale order
        order_01.sudo(self.user_not_allow.id).action_button_confirm()
        # Check sale order is confirmed
        self.assertNotEqual(order_01.state, 'draft')

        # Create invoice
        context = {
            'active_model': 'sale.order',
            'active_ids': [order_01.id],
            'active_id': order_01.id}
        wizard_invoice_id = self.sale_advance_obj.with_context(
            context).create({
                'advance_payment_method': 'all'})
        wizard_invoice_id.with_context(context).create_invoices()
        for invoice_id in order_01.invoice_ids:
            invoice_id.signal_workflow('invoice_open')
            # Check if invoice is open
            self.assertEqual(invoice_id.state, 'open')
            # Pay invoice
            invoice_id.pay_and_reconcile(
                invoice_id.amount_total, self.account_id.id,
                self.period_id.id, self.journal_id.id, self.account_id.id,
                self.period_id.id, self.journal_id.id,
                name="Payment for Invoice")
            # Check if invoice is paid
            self.assertTrue(order_01.invoiced)
            self.assertEqual(invoice_id.state, 'paid')

        # Create second order: no error because the previous invoice is already
        # paid
        order_02 = self.order_obj.create({
            'partner_id': self.partner_01.id})
        self.order_line_obj.create({
            'order_id': order_02.id,
            'product_id': self.product_01.id,
            'product_uom_qty': 1})
        # Confirm sale order
        order_02.sudo(self.user_not_allow.id).action_button_confirm()

        # Create third order: do not allow confirm because it has no limit.
        order_03 = self.order_obj.create({
            'partner_id': self.partner_01.id})
        self.order_line_obj.create({
            'order_id': order_03.id,
            'product_id': self.product_01.id,
            'product_uom_qty': 1})
        # Confirm sale order: catch raise warning
        self.assertRaises(
            UserError,
            order_03.sudo(self.user_not_allow.id).action_button_confirm)
