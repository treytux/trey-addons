###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import exceptions
from odoo.tests.common import TransactionCase


class TestSaleOrderMerge(TransactionCase):

    def setUp(self):
        super().setUp()
        self.partner_model = self.env['res.partner']
        self.product_model = self.env['product.product']
        self.sale_model = self.env['sale.order']
        self.sale_line_model = self.env['sale.order.line']
        self.warehouse_model = self.env['stock.warehouse']
        self.wiz_model = self.env['sale.order.merge']
        self.partner_01 = self.partner_model.create({
            'name': 'Partner Test 01',
        })
        self.partner_02 = self.partner_model.create({
            'name': 'Partner Test 02',
        })
        self.product_01 = self.product_model.create({
            'type': 'service',
            'company_id': False,
            'name': 'Service Product 01',
            'standard_price': 10,
            'list_price': 20,
        })
        self.product_02 = self.product_model.create({
            'type': 'service',
            'company_id': False,
            'name': 'Service Product 02',
            'standard_price': 25,
            'list_price': 50,
        })
        self.product_03 = self.product_model.create({
            'type': 'service',
            'company_id': False,
            'name': 'Service Product 03',
            'standard_price': 50,
            'list_price': 100,
        })
        self.warehouse_01 = self.warehouse_model.create({
            'name': 'Test Warehouse 01',
            'code': 'TW01',
        })
        self.warehouse_02 = self.warehouse_model.create({
            'name': 'Test Warehouse 02',
            'code': 'TW02',
        })

    def test_error_merge_orders_different_warehouses(self):
        sale_01 = self.sale_model.create({
            'partner_id': self.partner_01.id,
            'warehouse_id': self.warehouse_01.id,
        })
        line_01 = self.sale_line_model.new({
            'order_id': sale_01.id,
            'product_id': self.product_01.id,
            'product_uom_qty': 1,
            'price_unit': 19.99,
        })
        line_01.product_id_change()
        line_01.create(line_01._convert_to_write(line_01._cache))
        sale_02 = self.sale_model.create({
            'partner_id': self.partner_01.id,
            'warehouse_id': self.warehouse_02.id,
        })
        line_02 = self.sale_line_model.new({
            'order_id': sale_02.id,
            'product_id': self.product_01.id,
            'product_uom_qty': 1,
            'price_unit': 19.99,
        })
        line_02.product_id_change()
        line_02.create(line_02._convert_to_write(line_02._cache))
        wizard = self.wiz_model.with_context({
            'active_ids': [
                sale_01.id,
                sale_02.id,
            ],
        }).create({})
        with self.assertRaises(exceptions.UserError) as result:
            wizard.action_merge()
        self.assertEqual(
            result.exception.name,
            'You can only merge orders from the same warehouse',)
