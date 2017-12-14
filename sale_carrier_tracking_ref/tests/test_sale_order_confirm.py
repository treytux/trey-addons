# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp.tests import common
from openerp import fields
import logging
_log = logging.getLogger(__name__)


class TestSaleOrderConfirm(common.TransactionCase):

    def setUp(self):
        super(TestSaleOrderConfirm, self).setUp()
        self.partner_obj = self.env['res.partner']
        self.product_obj = self.env['product.product']
        self.product_tmpl_obj = self.env['product.template']
        self.order_obj = self.env['sale.order']
        self.order_line_obj = self.env['sale.order.line']

        # Create partner
        partner_data = {
            'name': 'Customer 01',
            'is_company': True,
            'customer': True,
            'email': 'customer1@test.com',
            'street': 'Calle Real, 33',
            'phone': '666225522'}
        self.partner_01 = self.partner_obj.create(partner_data)

        # Create products
        pt_01_data = {
            'name': 'Product 01',
            'type': 'product'}
        self.pt_01 = self.product_tmpl_obj.create(pt_01_data)
        pp_01_data = {'product_tmpl_id': self.pt_01.id}
        self.pp_01 = self.product_obj.create(pp_01_data)
        pt_02_data = {
            'name': 'Product 02',
            'type': 'product'}
        self.pt_02 = self.product_tmpl_obj.create(pt_02_data)
        pp_02_data = {'product_tmpl_id': self.pt_02.id}
        self.pp_02 = self.product_obj.create(pp_02_data)

        # Create sale order (with carrier tracking ref)
        order_01_data = {
            'partner_id': self.partner_01.id,
            'pricelist_id': self.ref('product.list0'),
            'section_id': self.ref('sales_team.section_sales_department'),
            'date_order': fields.Date.today(),
            'carrier_tracking_ref': 'aaaa'}
        self.order_01 = self.order_obj.create(order_01_data)

        # Create sale order lines
        order_line_01_data = {
            'order_id': self.order_01.id,
            'name': 'Description 1',
            'product_uom_qty': 1,
            'price_unit': 33.25,
            'product_uom': self.ref('product.product_uom_unit')}
        self.order_line_01 = self.order_line_obj.create(order_line_01_data)
        order_line_02_data = {
            'order_id': self.order_01.id,
            'product_id': self.pp_01.id,
            'product_uom_qty': 1,
            'product_uom': self.ref('product.product_uom_unit')}
        self.order_line_02 = self.order_line_obj.create(order_line_02_data)

        # Create sale order (without carrier tracking ref)
        order_02_data = {
            'partner_id': self.partner_01.id,
            'pricelist_id': self.ref('product.list0'),
            'section_id': self.ref('sales_team.section_sales_department'),
            'date_order': fields.Date.today()}
        self.order_02 = self.order_obj.create(order_02_data)

        # Create sale order lines
        order_line_01_data = {
            'order_id': self.order_02.id,
            'name': 'Description 1',
            'product_uom_qty': 1,
            'price_unit': 33.25,
            'product_uom': self.ref('product.product_uom_unit')}
        self.order_line_01 = self.order_line_obj.create(order_line_01_data)
        order_line_02_data = {
            'order_id': self.order_02.id,
            'product_id': self.pp_01.id,
            'product_uom_qty': 1,
            'product_uom': self.ref('product.product_uom_unit')}
        self.order_line_02 = self.order_line_obj.create(order_line_02_data)

    def test_sale_order_confirm_01(self):
        # Confirm sale order
        self.order_01.signal_workflow('order_confirm')
        # Check sale order state
        self.assertEqual(self.order_01.state, 'progress')
        # Check that picking has been created.
        self.assertEqual(len(self.order_01.picking_ids), 1)
        # Check carrier tracking ref.
        self.assertEqual(
            self.order_01.picking_ids[0].carrier_tracking_ref,
            self.order_01.carrier_tracking_ref)

    def test_sale_order_confirm_02(self):
        # Confirm sale order
        self.order_02.signal_workflow('order_confirm')
        # Check sale order state
        self.assertEqual(self.order_02.state, 'progress')
        # Check that picking has been created.
        self.assertEqual(len(self.order_02.picking_ids), 1)
        # Check carrier tracking ref.
        self.assertEqual(
            self.order_02.picking_ids[0].carrier_tracking_ref,
            self.order_02.carrier_tracking_ref)
