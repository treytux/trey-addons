import json
from datetime import timedelta

from odoo import fields
from odoo.tests.common import HttpCase


class TestWebsiteSaleAvailabilityByPo(HttpCase):

    def setUp(self):
        super().setUp()
        self.main_company = self.env.company
        self.main_company.write({
            'stock_field': 'qty_available',
        })
        self.product = self.env['product.product'].create({
            'name': 'Test Product',
            'company_id': self.main_company.id,
            'type': 'product',
        })
        self.template = self.product.product_tmpl_id
        self.warehouse_stock_loc = self.env.ref('stock.stock_location_stock')

    def _update_product_stock(self, quantity):
        self.env['stock.quant'].search([
            ('product_id', '=', self.product.id),
        ]).unlink()
        if quantity > 0:
            self.env['stock.quant'].with_context(inventory_mode=True).create({
                'product_id': self.product.id,
                'location_id': self.warehouse_stock_loc.id,
                'inventory_quantity': quantity,
            }).action_apply_inventory()
        self.product.invalidate_recordset([
            'qty_available', 'virtual_available', 'stock_state'])

    def test_compute_stock_state(self):
        self.template.write({
            'show_availability': True,
            'available_threshold': 20,
        })
        self._update_product_stock(30)
        self.assertEqual(self.product.stock_state, 'available')
        self._update_product_stock(15)
        self.assertEqual(self.product.stock_state, 'latest_units')
        self._update_product_stock(0)
        picking_type_in = self.env.ref('stock.picking_type_in')
        supplier_loc = self.env.ref('stock.stock_location_suppliers')
        move = self.env['stock.move'].create({
            'name': 'Test Incoming Move',
            'product_id': self.product.id,
            'product_uom_qty': 5,
            'product_uom': self.product.uom_id.id,
            'location_id': supplier_loc.id,
            'location_dest_id': self.warehouse_stock_loc.id,
            'picking_type_id': picking_type_in.id,
        })
        move._action_confirm()
        self.product.invalidate_recordset(['virtual_available', 'stock_state'])
        self.assertEqual(self.product.stock_state, 'coming_soon')
        move._action_cancel()
        self._update_product_stock(0)
        self.assertEqual(self.product.stock_state, 'not_available')

    def test_get_availability_purchase_filters(self):
        self._update_product_stock(0)
        partner = self.env['res.partner'].create({'name': 'Test Partner'})
        now = fields.Datetime.now()
        po_valid = self.env['purchase.order'].create({
            'partner_id': partner.id,
            'date_planned_public': True,
        })
        po_valid.write({
            'state': 'purchase',
        })
        line_valid = self.env['purchase.order.line'].create({
            'order_id': po_valid.id,
            'product_id': self.product.id,
            'product_qty': 10,
            'price_unit': 50.0,
            'date_planned': now + timedelta(days=5),
        })
        po_private = self.env['purchase.order'].create({
            'partner_id': partner.id,
            'date_planned_public': False,
        })
        po_private.write({'state': 'purchase'})
        self.env['purchase.order.line'].create({
            'order_id': po_private.id,
            'product_id': self.product.id,
            'product_qty': 10,
            'price_unit': 50.0,
            'date_planned': now + timedelta(days=2),
        })
        po_draft = self.env['purchase.order'].create({
            'partner_id': partner.id,
            'date_planned_public': True,
        })
        self.env['purchase.order.line'].create({
            'order_id': po_draft.id,
            'product_id': self.product.id,
            'product_qty': 10,
            'price_unit': 50.0,
            'date_planned': now + timedelta(days=1),
        })
        po_past = self.env['purchase.order'].create({
            'partner_id': partner.id,
            'date_planned_public': True,
        })
        po_past.write({'state': 'purchase'})

        self.env['purchase.order.line'].create({
            'order_id': po_past.id,
            'product_id': self.product.id,
            'product_qty': 10,
            'price_unit': 50.0,
            'date_planned': now - timedelta(days=2),
        })
        po_received = self.env['purchase.order'].create({
            'partner_id': partner.id,
            'date_planned_public': True,
        })
        po_received.write({'state': 'purchase'})
        line_received = self.env['purchase.order.line'].create({
            'order_id': po_received.id,
            'product_id': self.product.id,
            'product_qty': 10,
            'price_unit': 50.0,
            'date_planned': now + timedelta(days=3),
        })
        line_received.write({'qty_received': 11})
        self.product.invalidate_recordset(['stock_state', 'virtual_available'])
        result = self.product.get_availability()
        self.assertIn(self.product.id, result)
        self.assertEqual(
            result[self.product.id]['date_planned'], line_valid.date_planned)

    def test_get_availability_purchase_available_shortly(self):
        self._update_product_stock(0)
        partner = self.env['res.partner'].create({'name': 'Test Partner'})
        now = fields.Datetime.now()
        po_valid = self.env['purchase.order'].create({
            'partner_id': partner.id,
            'date_planned_public': True,
        })
        po_valid.write({'state': 'purchase'})
        self.env['purchase.order.line'].create({
            'order_id': po_valid.id,
            'product_id': self.product.id,
            'product_qty': 10,
            'price_unit': 50.0,
            'date_planned': now - timedelta(days=1),
        })
        self.product.invalidate_recordset(['stock_state', 'virtual_available'])
        result = self.product.get_availability()
        self.assertEqual(
            result[self.product.id]['stock_state'], 'available_shortly')
        self.assertFalse(result[self.product.id]['date_planned'])

    def test_product_availability_controller(self):
        fake_id = 999999
        product_ids = [self.product.id, fake_id]
        response = self.url_open(
            '/shop/product_availability',
            data=json.dumps({'params': {'product_ids': product_ids}}),
            headers={'Content-Type': 'application/json'})
        self.assertEqual(response.status_code, 200)
        response_json = response.json()
        self.assertIn('result', response_json)
        data = response_json['result']
        self.assertIn(str(self.product.id), data)
        self.assertNotIn(str(fake_id), data)
        self.template.write({
            'show_availability': True,
            'available_threshold': 10,
        })
        picking_type_in = self.env.ref('stock.picking_type_in')
        supplier_loc = self.env.ref('stock.stock_location_suppliers')
        move = self.env['stock.move'].create({
            'name': 'Test Controller Move',
            'product_id': self.product.id,
            'product_uom_qty': 5,
            'product_uom': self.product.uom_id.id,
            'location_id': supplier_loc.id,
            'location_dest_id': self.warehouse_stock_loc.id,
            'picking_type_id': picking_type_in.id,
        })
        move._action_confirm()
        self.product.invalidate_recordset(['stock_state', 'virtual_available'])
        response_no_date = self.url_open(
            '/shop/product_availability',
            data=json.dumps({'params': {'product_ids': [self.product.id]}}),
            headers={'Content-Type': 'application/json'})
        data_no_date = response_no_date.json()['result']
        product_info = data_no_date[str(self.product.id)]
        self.assertEqual(product_info['stock_state'], 'coming_soon')
        self.assertFalse(product_info['date_planned'])
