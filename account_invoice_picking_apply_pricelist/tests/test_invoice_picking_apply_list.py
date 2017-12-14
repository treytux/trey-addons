# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp.tests.common import TransactionCase
from openerp import fields, exceptions, _


class TestStockPickingInvoice(TransactionCase):
    def setUp(self):
        super(TestStockPickingInvoice, self).setUp()
        self.pricelists = self.env['product.pricelist'].search([])
        self.pricelist_1 = self.pricelists and self.pricelists[0] or False
        self.pricelist_2 = self.pricelists and self.pricelists[1] or False
        self.supplier_location = self.env[
            'ir.model.data'].xmlid_to_res_id(
                'stock.stock_location_suppliers')
        self.stock_locations = self.env['stock.location'].search([])
        self.location1 = (self.stock_locations and
                          self.stock_locations[0] or False)
        self.location2 = (self.stock_locations and
                          self.stock_locations[1] or False)
        self.productA = self.env['product.product'].create({
            'name': 'Product A',
            'list_price': 10.0})
        self.productB = self.env['product.product'].create({
            'name': 'Product B',
            'list_price': 10.0})
        self.account_positions = self.env[
            'account.fiscal.position'].search([])
        self.account_position_fiscal = (self.account_positions and
                                        self.account_positions[0] or False)
        self.partner = self.env['res.partner'].create({
            'name': 'Test partner',
            'property_account_position': self.account_position_fiscal.id})
        self.picking_in_0 = self.env['stock.picking'].create({
            'partner_id': self.partner.id,
            'picking_type_id': self.env.ref('stock.picking_type_in').id,
            'pricelist_id': self.pricelist_1 and self.pricelist_1.id or False,
            'invoice_state': '2binvoiced'})
        self.picking_in_01 = self.env['stock.picking'].create({
            'partner_id': self.partner.id,
            'picking_type_id': self.env.ref('stock.picking_type_in').id,
            'invoice_state': '2binvoiced'})
        self.env['stock.move'].create({
            'name': self.productA.name,
            'product_id': self.productA.id,
            'product_uom_qty': 1,
            'product_uom': self.productA.uom_id.id,
            'picking_id': self.picking_in_0.id,
            'location_id': self.location1.id,
            'location_dest_id': self.location2.id,
            'invoice_state': '2binvoiced'})
        self.env['stock.move'].create({
            'name': self.productB.name,
            'product_id': self.productB.id,
            'product_uom_qty': 1,
            'product_uom': self.productB.uom_id.id,
            'picking_id': self.picking_in_0.id,
            'location_id': self.location1.id,
            'location_dest_id': self.location2.id,
            'invoice_state': '2binvoiced'})
        self.env['stock.move'].create({
            'name': self.productA.name,
            'product_id': self.productA.id,
            'product_uom_qty': 1,
            'product_uom': self.productA.uom_id.id,
            'picking_id': self.picking_in_01.id,
            'location_id': self.location1.id,
            'location_dest_id': self.location2.id,
            'invoice_state': '2binvoiced'})
        self.env['stock.move'].create({
            'name': self.productB.name,
            'product_id': self.productB.id,
            'product_uom_qty': 1,
            'product_uom': self.productB.uom_id.id,
            'picking_id': self.picking_in_01.id,
            'location_id': self.location1.id,
            'location_dest_id': self.location2.id,
            'invoice_state': '2binvoiced'})
        self.saleorder1 = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'picking_policy': 'one',
            'order_policy': 'picking',
            'pricelist_id': self.pricelist_1 and self.pricelist_1.id or False,
            'order_line': [
                (0, 0, {'product_id': self.productA.id,
                        'product_uom_qty': 8.0})]})
        self.saleorder2 = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'picking_policy': 'one',
            'pricelist_id': self.pricelist_2 and self.pricelist_2.id or False,
            'order_policy': 'picking',
            'order_line': [
                (0, 0, {'product_id': self.productA.id,
                        'product_uom_qty': 8.0})]})
        self.purchaseorder1 = self.env['purchase.order'].create({
            'partner_id': self.partner.id,
            'location_id': self.supplier_location,
            'pricelist_id': self.pricelist_1 and self.pricelist_1.id or False})
        self.purchaseorderline1 = self.env['purchase.order.line'].create({
            'product_id': self.productA.id,
            'name': self.productA.name,
            'product_qty': 1,
            'order_id': self.purchaseorder1.id,
            'price_unit': self.productA.product_tmpl_id.list_price,
            'date_planned': fields.Date.today()})
        self.purchaseorder2 = self.env['purchase.order'].create({
            'partner_id': self.partner.id,
            'pricelist_id': self.pricelist_2 and self.pricelist_2.id or False,
            'location_id': self.supplier_location})
        self.purchaseorderline2 = self.env['purchase.order.line'].create({
            'product_id': self.productB.id,
            'name': self.productB.name,
            'product_qty': 1,
            'order_id': self.purchaseorder2.id,
            'price_unit': self.productB.product_tmpl_id.list_price,
            'date_planned': fields.Date.today()})
        self.companies = self.env['res.company'].search([])
        if not self.companies:
            raise exceptions.Warning(_('There is no company'))
        self.company_id = self.companies[0].id
        self.acc_journals = self.env['account.journal'].search([
            ('type', '=', 'sale'),
            ('company_id', '=', self.company_id)])
        self.saleorder1.signal_workflow('order_confirm')
        payment = self.env['sale.advance.payment.inv'].create({
            'advance_payment_method': 'all'})
        payment.with_context(active_model='sale.order',
                             active_ids=[self.saleorder1.id],
                             active_id=self.saleorder1.id).create_invoices()
        for invoice in self.saleorder1.invoice_ids:
            invoice.date_invoice = fields.Date.today()
            invoice.signal_workflow('invoice_open')
        self.saleorder2.signal_workflow('order_confirm')
        payment.with_context(active_model='sale.order',
                             active_ids=[self.saleorder2.id],
                             active_id=self.saleorder2.id).create_invoices()
        for invoice in self.saleorder2.invoice_ids:
            invoice.date_invoice = fields.Date.today()
            invoice.signal_workflow('invoice_open')
        self.purchaseorder1.signal_workflow('order_confirm')
        self.purchaseorder1.wkf_confirm_order()
        self.picking_in_3_id = self.purchaseorder1.action_picking_create()
        for invoice in self.purchaseorder1.invoice_ids:
            invoice.date_invoice = fields.Date.today()
            invoice.signal_workflow('invoice_open')
        self.purchaseorder2.signal_workflow('order_confirm')
        self.purchaseorder2.wkf_confirm_order()
        self.picking_in_4_id = self.purchaseorder2.action_picking_create()
        for invoice in self.purchaseorder2.invoice_ids:
            invoice.date_invoice = fields.Date.today()
            invoice.signal_workflow('invoice_open')
        pickings = self.env['stock.picking'].search([])
        self.picking_in_1 = pickings.filtered(
            lambda x: x.sale_id == self.saleorder1)
        self.picking_in_2 = pickings.filtered(
            lambda x: x.sale_id == self.saleorder2)
        self.picking_in_3 = self.env[
            'stock.picking'].browse(self.picking_in_3_id)
        self.picking_in_3.write({'invoice_state': '2binvoiced'})
        self.picking_in_4 = self.env[
            'stock.picking'].browse(self.picking_in_4_id)
        self.picking_in_4.write({'invoice_state': '2binvoiced'})

    def test_01(self):
        '''Direct invoicing with pricelist'''
        self.assertEqual(self.picking_in_0.invoice_state, '2binvoiced')
        self.picking_in_0.action_confirm()
        self.picking_in_0.action_assign()
        self.picking_in_0.do_prepare_partial()
        self.picking_in_0.do_transfer()
        self.assertEqual(self.picking_in_0.state, 'done')
        wizard = self.env['stock.invoice.onshipping'].with_context({
            'active_ids': [self.picking_in_0.id],
            'active_model': 'stock.picking',
            'active_id': self.picking_in_0.id}).create(
                {'journal_id': self.acc_journals and
                    self.acc_journals[0].id or False})
        wizard.create_invoice()
        self.assertEqual(self.picking_in_0.invoice_state, 'invoiced')
        for move in self.picking_in_0.move_lines:
            self.assertEqual(move.invoice_state, 'invoiced')

    def test_02(self):
        '''Direct invoicing without pricelist'''
        self.assertEqual(self.picking_in_01.invoice_state, '2binvoiced')
        self.picking_in_01.action_confirm()
        self.picking_in_01.action_assign()
        self.picking_in_01.do_prepare_partial()
        self.picking_in_01.do_transfer()
        self.assertEqual(self.picking_in_01.state, 'done')
        wizard = self.env['stock.invoice.onshipping'].with_context({
            'active_ids': [self.picking_in_01.id],
            'active_model': 'stock.picking',
            'active_id': self.picking_in_01.id}).create(
                {'journal_id': self.acc_journals and
                    self.acc_journals[0].id or False})
        self.assertRaises(Exception, wizard.create_invoice)

    def test_03(self):
        '''Invoicing from sale order with pricelist'''
        self.assertEqual(len(self.picking_in_1), 1, 'Picking not found')
        self.assertEqual(self.picking_in_1.invoice_state, '2binvoiced')
        self.picking_in_1.action_confirm()
        self.picking_in_1.action_assign()
        self.picking_in_1.do_prepare_partial()
        self.picking_in_1.do_transfer()
        self.assertEqual(self.picking_in_1.state, 'done')
        wizard = self.env['stock.invoice.onshipping'].with_context({
            'active_ids': [self.picking_in_1.id],
            'active_model': 'stock.picking',
            'active_id': self.picking_in_1.id}).create(
                {'journal_id': self.acc_journals and
                    self.acc_journals[0].id or False})
        wizard.create_invoice()
        self.assertEqual(self.picking_in_1.invoice_state, 'invoiced')
        for move in self.picking_in_1.move_lines:
            self.assertEqual(move.invoice_state, 'invoiced')

    def test_04(self):
        '''Invoicing from sale order without pricelist'''
        self.assertEqual(len(self.picking_in_2), 1, 'Picking not found')
        self.assertEqual(self.picking_in_2.invoice_state, '2binvoiced')
        self.picking_in_2.action_confirm()
        self.picking_in_2.action_assign()
        self.picking_in_2.do_prepare_partial()
        self.picking_in_2.do_transfer()
        self.assertEqual(self.picking_in_2.state, 'done')
        wizard = self.env['stock.invoice.onshipping'].with_context({
            'active_ids': [self.picking_in_2.id],
            'active_model': 'stock.picking',
            'active_id': self.picking_in_2.id}).create(
                {'journal_id': self.acc_journals and
                    self.acc_journals[0].id or False})
        wizard.create_invoice()
        self.assertEqual(self.picking_in_2.invoice_state, 'invoiced')
        for move in self.picking_in_2.move_lines:
            self.assertEqual(move.invoice_state, 'invoiced')

    def test_05(self):
        '''Invoicing from purchase order with pricelist'''
        self.assertEqual(len(self.picking_in_3), 1, 'Picking not found')
        self.assertEqual(self.picking_in_3.invoice_state, '2binvoiced')
        self.picking_in_3.action_confirm()
        self.picking_in_3.action_assign()
        self.picking_in_3.do_prepare_partial()
        self.picking_in_3.do_transfer()
        self.assertEqual(self.picking_in_3.state, 'done')
        wizard = self.env['stock.invoice.onshipping'].with_context({
            'active_ids': [self.picking_in_3.id],
            'active_model': 'stock.picking',
            'active_id': self.picking_in_3.id}).create(
                {'journal_id': self.acc_journals and
                    self.acc_journals[0].id or False})
        wizard.create_invoice()
        self.assertEqual(self.picking_in_3.invoice_state, 'invoiced')
        for move in self.picking_in_3.move_lines:
            self.assertEqual(move.invoice_state, 'invoiced')

    def test_06(self):
        '''Invoicing from purchase order without pricelist'''
        self.assertEqual(len(self.picking_in_4), 1, 'Picking not found')
        self.assertEqual(self.picking_in_4.invoice_state, '2binvoiced')
        self.picking_in_4.action_confirm()
        self.picking_in_4.action_assign()
        self.picking_in_4.do_prepare_partial()
        self.picking_in_4.do_transfer()
        self.assertEqual(self.picking_in_4.state, 'done')
        wizard = self.env['stock.invoice.onshipping'].with_context({
            'active_ids': [self.picking_in_4.id],
            'active_model': 'stock.picking',
            'active_id': self.picking_in_4.id}).create(
                {'journal_id': self.acc_journals and
                    self.acc_journals[0].id or False})
        wizard.create_invoice()
        self.assertEqual(self.picking_in_4.invoice_state, 'invoiced')
        for move in self.picking_in_4.move_lines:
            self.assertEqual(move.invoice_state, 'invoiced')

    def test_07(self):
        '''Test compare price unit with diferent pricelist'''
        self.invoice_0 = self.picking_in_0.invoice_id
        self.invoice_01 = self.picking_in_01.invoice_id
        self.invoice_1 = self.picking_in_1.invoice_id
        self.invoice_2 = self.picking_in_2.invoice_id
        self.invoice_3 = self.picking_in_3.invoice_id
        self.invoice_4 = self.picking_in_4.invoice_id
        for line0, line1 in zip(
                self.invoice_0.invoice_line, self.invoice_01.invoice_line):
            self.assertNotEqual(line0.price_unit, line1.price_unit)
        for line0, line1 in zip(
                self.invoice_0.invoice_line, self.invoice_1.invoice_line):
            self.assertEqual(line0.price_unit, line1.price_unit)
        for line0, line1 in zip(
                self.invoice_0.invoice_line, self.invoice_2.invoice_line):
            self.assertNotEqual(line0.price_unit, line1.price_unit)
        for line0, line1 in zip(
                self.invoice_0.invoice_line, self.invoice_3.invoice_line):
            self.assertEqual(line0.price_unit, line1.price_unit)
        for line0, line1 in zip(
                self.invoice_0.invoice_line, self.invoice_4.invoice_line):
            self.assertNotEqual(line0.price_unit, line1.price_unit)
        for line0, line1 in zip(
                self.invoice_01.invoice_line, self.invoice_1.invoice_line):
            self.assertEqual(line0.price_unit, line1.price_unit)
        for line0, line1 in zip(
                self.invoice_01.invoice_line, self.invoice_2.invoice_line):
            self.assertNotEqual(line0.price_unit, line1.price_unit)
        for line0, line1 in zip(
                self.invoice_01.invoice_line, self.invoice_3.invoice_line):
            self.assertEqual(line0.price_unit, line1.price_unit)
        for line0, line1 in zip(
                self.invoice_01.invoice_line, self.invoice_4.invoice_line):
            self.assertNotEqual(line0.price_unit, line1.price_unit)
