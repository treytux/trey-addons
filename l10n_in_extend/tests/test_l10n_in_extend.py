###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests.common import TransactionCase


class TestL10nInExtend(TransactionCase):

    def setUp(self):
        super().setUp()
        self.partner = self.env['res.partner'].create({
            'name': 'Test Partner',
        })
        self.product = self.env['product.product'].create({
            'name': 'Test Product',
            'type': 'service',
            'company_id': False,
        })
        self.journal_sale = self.env['account.journal'].create({
            'name': 'Test journal for sale',
            'type': 'sale',
            'code': 'TSALE',
        })
        self.account_income = self.env['account.account'].create({
            'name': 'Test Income Account',
            'code': 'TESTINC001',
            'account_type': 'income',
            'company_id': self.env.company.id,
            'reconcile': False,
        })
        self.transport_vals = {
            'transport_mode': 'Road',
            'vehicle_number': 'HR-26-BK-1234',
            'supply_date': '2024-01-15',
            'supply_place': 'Mumbai Warehouse',
        }

    def test_fields_exist_on_account_move(self):
        self.assertIn('transport_mode', self.env['account.move']._fields)
        self.assertIn('vehicle_number', self.env['account.move']._fields)
        self.assertIn('supply_date', self.env['account.move']._fields)
        self.assertIn('supply_place', self.env['account.move']._fields)
        invoice = self.env['account.move'].new({
            'move_type': 'out_invoice',
            'partner_id': self.partner.id,
            **self.transport_vals,
        })
        for field, value in self.transport_vals.items():
            self.assertEqual(
                invoice[field], value,
                'Field %s should be %s but got %s' % (
                    field, value, invoice[field]))

    def test_fields_exist_on_purchase_order(self):
        purchase_order = self.env['purchase.order'].create({
            'partner_id': self.partner.id,
            'order_line': [(0, 0, {
                'product_id': self.product.id,
                'name': self.product.name,
                'price_unit': 100,
                'product_qty': 1,
                'product_uom': self.product.uom_id.id,
            })],
            **self.transport_vals,
        })
        for field, value in self.transport_vals.items():
            self.assertEqual(
                purchase_order[field], value,
                'Field %s should be %s but got %s' % (
                    field, value, purchase_order[field]))

    def test_fields_exist_on_sale_order(self):
        sale_order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [(0, 0, {
                'product_id': self.product.id,
                'price_unit': 100,
                'product_uom_qty': 1,
            })],
            **self.transport_vals,
        })
        for field, value in self.transport_vals.items():
            self.assertEqual(
                sale_order[field], value,
                'Field %s should be %s but got %s' % (
                    field, value, sale_order[field]))

    def test_purchase_order_prepare_invoice_propagates_fields(self):
        purchase_order = self.env['purchase.order'].create({
            'partner_id': self.partner.id,
            'order_line': [(0, 0, {
                'product_id': self.product.id,
                'name': self.product.name,
                'price_unit': 100,
                'product_qty': 1,
                'product_uom': self.product.uom_id.id,
            })],
            **self.transport_vals,
        })
        invoice_vals = purchase_order._prepare_invoice()
        for field, value in self.transport_vals.items():
            self.assertEqual(
                invoice_vals[field], value,
                'Field %s should be %s in invoice vals but got %s' % (
                    field, value, invoice_vals.get(field)))

    def test_sale_order_prepare_invoice_propagates_fields(self):
        sale_order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [(0, 0, {
                'product_id': self.product.id,
                'price_unit': 100,
                'product_uom_qty': 1,
            })],
            **self.transport_vals,
        })
        invoice_vals = sale_order._prepare_invoice()
        for field, value in self.transport_vals.items():
            self.assertEqual(
                invoice_vals[field], value,
                'Field %s should be %s in invoice vals but got %s' % (
                    field, value, invoice_vals.get(field)))
