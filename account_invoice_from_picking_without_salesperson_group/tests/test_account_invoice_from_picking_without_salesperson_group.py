# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp.tests import common


class TestAccountInvoiceFromPickingWithoutSalespersonGroup(
        common.TransactionCase):

    def setUp(self):
        super(
            TestAccountInvoiceFromPickingWithoutSalespersonGroup, self).setUp()
        base_company_id = self.ref('base.main_company')
        base_pricelist_id = self.ref('product.list0')
        self.partner_01 = self.env['res.partner'].create({
            'name': 'Partner 01',
            'customer': False,
            'company_id': base_company_id})
        self.user_01 = self.env['res.users'].create({
            'partner_id': self.partner_01.id,
            'login': 'user01@test.es',
            'password': 'a',
            'company_id': base_company_id})
        self.partner_02 = self.env['res.partner'].create({
            'name': 'Partner 02',
            'customer': False,
            'company_id': base_company_id})
        self.user_02 = self.env['res.users'].create({
            'partner_id': self.partner_02.id,
            'login': 'user02@test.es',
            'password': 'a',
            'company_id': base_company_id})
        self.customer_01 = self.env['res.partner'].create({
            'name': 'Customer 01',
            'customer': True})
        self.pt_01 = self.env['product.template'].create({
            'name': 'Product 01',
            'type': 'product'})
        self.pp_01 = self.env['product.product'].create({
            'product_tmpl_id': self.pt_01.id,
            'list_price': 100})
        self.order_01 = self.env['sale.order'].create({
            'partner_id': self.customer_01.id,
            'pricelist_id': base_pricelist_id,
            'order_policy': 'picking',
            'user_id': self.user_01.id,
            'order_line': [
                (0, 0, {'product_id': self.pp_01.id,
                        'product_uom_qty': 1.0})]})
        self.order_02 = self.env['sale.order'].create({
            'partner_id': self.customer_01.id,
            'pricelist_id': base_pricelist_id,
            'order_policy': 'picking',
            'user_id': self.user_02.id,
            'order_line': [
                (0, 0, {'product_id': self.pp_01.id,
                        'product_uom_qty': 2.0})]})

        self.order_01.signal_workflow('order_confirm')
        self.assertEqual(len(self.order_01.picking_ids), 1)
        self.picking_01 = self.order_01.picking_ids[0]
        self.assertEqual(self.picking_01.invoice_state, '2binvoiced')
        self.picking_01.action_confirm()
        self.picking_01.force_assign()
        self.picking_01.do_transfer()
        self.assertEqual(self.picking_01.state, 'done')

        self.order_02.signal_workflow('order_confirm')
        self.assertEqual(len(self.order_02.picking_ids), 1)
        self.picking_02 = self.order_02.picking_ids[0]
        self.assertEqual(self.picking_02.invoice_state, '2binvoiced')
        self.picking_02.action_confirm()
        self.picking_02.force_assign()
        self.picking_02.do_transfer()
        self.assertEqual(self.picking_02.state, 'done')

        self.acc_sale_journal = self.env['account.journal'].search([
            ('type', '=', 'sale'), ('company_id', '=', base_company_id)],
            limit=1)
        self.assertEqual(len(self.acc_sale_journal), 1)

    def test_sale_order_invoice_group_with_different_salesperson(self):
        wizard = self.env['stock.invoice.onshipping'].with_context({
            'active_ids': [self.picking_01.id, self.picking_02.id],
            'active_model': 'stock.picking',
            'active_id': self.picking_01.id}).create({
                'journal_id': self.acc_sale_journal.id,
                'group': True})
        wizard.create_invoice()
        self.assertEqual(self.picking_01.invoice_state, 'invoiced')
        self.assertEqual(self.picking_02.invoice_state, 'invoiced')
        self.assertEqual(self.order_01.invoice_ids, self.order_02.invoice_ids)
        self.assertEqual(
            self.order_01.invoice_ids[0].user_id, self.order_01.user_id)

    def test_sale_order_invoice_no_group_with_different_salesperson(self):
        wizard = self.env['stock.invoice.onshipping'].with_context({
            'active_ids': [self.picking_01.id, self.picking_02.id],
            'active_model': 'stock.picking',
            'active_id': self.picking_01.id}).create({
                'journal_id': self.acc_sale_journal.id,
                'group': False})
        wizard.create_invoice()
        self.assertEqual(self.picking_01.invoice_state, 'invoiced')
        self.assertEqual(self.picking_02.invoice_state, 'invoiced')
        self.assertNotEqual(
            self.order_01.invoice_ids, self.order_02.invoice_ids)
        self.assertEqual(len(self.order_01.invoice_ids), 1)
        self.assertEqual(len(self.order_02.invoice_ids), 1)
        self.assertEqual(
            self.order_01.invoice_ids[0].user_id, self.order_01.user_id)
        self.assertEqual(
            self.order_02.invoice_ids[0].user_id, self.order_02.user_id)

    def test_sale_order_invoice_group_with_equal_salesperson(self):
        self.order_02.user_id = self.user_01.id
        wizard = self.env['stock.invoice.onshipping'].with_context({
            'active_ids': [self.picking_01.id, self.picking_02.id],
            'active_model': 'stock.picking',
            'active_id': self.picking_01.id}).create({
                'journal_id': self.acc_sale_journal.id,
                'group': True})
        wizard.create_invoice()
        self.assertEqual(self.picking_01.invoice_state, 'invoiced')
        self.assertEqual(self.picking_02.invoice_state, 'invoiced')
        self.assertEqual(self.order_01.invoice_ids, self.order_02.invoice_ids)
        self.assertEqual(
            self.order_01.invoice_ids[0].user_id, self.order_01.user_id)

    def test_sale_order_invoice_no_group_with_equal_salesperson(self):
        self.order_02.user_id = self.user_01.id
        wizard = self.env['stock.invoice.onshipping'].with_context({
            'active_ids': [self.picking_01.id, self.picking_02.id],
            'active_model': 'stock.picking',
            'active_id': self.picking_01.id}).create({
                'journal_id': self.acc_sale_journal.id,
                'group': False})
        wizard.create_invoice()
        self.assertEqual(self.picking_01.invoice_state, 'invoiced')
        self.assertEqual(self.picking_02.invoice_state, 'invoiced')
        self.assertNotEqual(
            self.order_01.invoice_ids, self.order_02.invoice_ids)
        self.assertEqual(len(self.order_01.invoice_ids), 1)
        self.assertEqual(len(self.order_02.invoice_ids), 1)
        self.assertEqual(
            self.order_01.invoice_ids[0].user_id, self.order_01.user_id)
        self.assertEqual(
            self.order_02.invoice_ids[0].user_id, self.order_02.user_id)
