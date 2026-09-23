###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from dateutil.relativedelta import relativedelta
from odoo import fields
from odoo.tests.common import TransactionCase


class TestStockOrderpointPeriodQty(TransactionCase):

    def setUp(self):
        super().setUp()
        self.company = self.env.company
        self.warehouse = self.env.ref('stock.warehouse0')
        self.product = self.env['product.template'].create({
            'name': 'Period demand product',
            'type': 'product',
        }).product_variant_id
        self.orderpoint = self.env['stock.warehouse.orderpoint'].create({
            'warehouse_id': self.warehouse.id,
            'location_id': self.warehouse.lot_stock_id.id,
            'product_id': self.product.id,
            'product_min_qty': 0,
            'product_max_qty': 0,
        })

    def assert_historical_quantities(self, orderpoint, period, month):
        orderpoint._compute_historical_quantities()
        self.assertEqual(orderpoint.product_min_qty_period, period)
        self.assertEqual(orderpoint.product_min_qty_month, month)

    def create_validated_move(
            self, picking_type, location, location_dest, quantity,
            company=None):
        picking_model = self.env['stock.picking']
        move_model = self.env['stock.move']
        if company:
            picking_model = picking_model.with_company(company)
            move_model = move_model.with_company(company)
        picking = picking_model.create({
            'picking_type_id': picking_type.id,
            'location_id': location.id,
            'location_dest_id': location_dest.id,
        })
        move = move_model.create({
            'name': 'Period demand test move',
            'picking_id': picking.id,
            'product_id': self.product.id,
            'product_uom': self.product.uom_id.id,
            'product_uom_qty': quantity,
            'location_id': location.id,
            'location_dest_id': location_dest.id,
        })
        picking.action_confirm()
        picking.action_assign()
        move.quantity_done = quantity
        picking.button_validate()
        return move

    def create_cancelled_move(
            self, picking_type, location, location_dest, quantity):
        picking = self.env['stock.picking'].create({
            'picking_type_id': picking_type.id,
            'location_id': location.id,
            'location_dest_id': location_dest.id,
        })
        move = self.env['stock.move'].create({
            'name': 'Cancelled period demand test move',
            'picking_id': picking.id,
            'product_id': self.product.id,
            'product_uom': self.product.uom_id.id,
            'product_uom_qty': quantity,
            'location_id': location.id,
            'location_dest_id': location_dest.id,
        })
        picking.action_confirm()
        move._action_cancel()
        return move

    def create_inventory(self, location, quantity):
        self.env['stock.quant']._update_available_quantity(
            self.product, location, quantity)

    def create_deposit_location(self):
        deposit_parent = self.env['stock.location'].create({
            'name': 'Period demand deposit parent',
            'location_id': self.warehouse.view_location_id.id,
            'usage': 'view',
        })
        deposit_location = self.env['stock.location'].create({
            'name': 'Period demand deposit',
            'location_id': deposit_parent.id,
            'usage': 'internal',
        })
        self.warehouse.int_type_id.active = True
        self.warehouse.deposit_parent_id = deposit_parent
        return deposit_location

    def test_monthly_replenishment_after_purchase_and_sale(self):
        self.company.period_min_qty = 'monthly'
        supplier_location = self.env.ref('stock.stock_location_suppliers')
        customer_location = self.env.ref('stock.stock_location_customers')
        self.create_validated_move(
            self.warehouse.in_type_id, supplier_location,
            self.warehouse.lot_stock_id, 10)
        self.create_validated_move(
            self.warehouse.out_type_id, self.warehouse.lot_stock_id,
            customer_location, 8)
        self.assertEqual(self.orderpoint.qty_on_hand, 2)
        self.assertEqual(self.orderpoint.qty_forecast, 2)
        self.assertEqual(self.orderpoint._get_historical_monthly_demand(), 8)
        self.assertEqual(self.orderpoint.product_min_qty_period, 8)
        self.assertEqual(self.orderpoint.product_min_qty_month, 8)
        self.orderpoint._compute_qty_to_order()
        self.assertEqual(self.orderpoint.qty_to_order, 6)
        self.assert_historical_quantities(self.orderpoint, 8, 8)

    def test_period_and_month_demands_are_different(self):
        self.company.period_min_qty = 'annual'
        customer_location = self.env.ref('stock.stock_location_customers')
        move = self.create_validated_move(
            self.warehouse.out_type_id,
            self.warehouse.lot_stock_id, customer_location, 12)
        move.date = fields.Datetime.now() - relativedelta(months=2)
        self.orderpoint._compute_historical_quantities()
        self.assertEqual(self.orderpoint.product_min_qty_period, 1)
        self.assertEqual(self.orderpoint.product_min_qty_month, 0)
        self.assert_historical_quantities(self.orderpoint, 1, 0)

    def test_no_sales_does_not_order_supplier_receipts(self):
        self.company.period_min_qty = 'monthly'
        supplier_location = self.env.ref('stock.stock_location_suppliers')
        self.create_validated_move(
            self.warehouse.in_type_id, supplier_location,
            self.warehouse.lot_stock_id, 10)
        self.assertEqual(self.orderpoint.qty_on_hand, 10)
        self.assertEqual(
            self.orderpoint._get_historical_monthly_demand(), 0)
        self.orderpoint._compute_qty_to_order()
        self.assertEqual(self.orderpoint.qty_to_order, 0)
        self.assert_historical_quantities(self.orderpoint, 0, 0)

    def test_quarterly_replenishment_after_purchase_and_sale(self):
        self.company.period_min_qty = 'quarterly'
        supplier_location = self.env.ref('stock.stock_location_suppliers')
        customer_location = self.env.ref('stock.stock_location_customers')
        self.create_validated_move(
            self.warehouse.in_type_id, supplier_location,
            self.warehouse.lot_stock_id, 10)
        self.create_validated_move(
            self.warehouse.out_type_id, self.warehouse.lot_stock_id,
            customer_location, 8)
        self.assertEqual(self.orderpoint.qty_forecast, 2)
        self.assertEqual(self.orderpoint._get_historical_monthly_demand(), 3)
        self.orderpoint._compute_qty_to_order()
        self.assertEqual(self.orderpoint.qty_to_order, 1)
        self.assert_historical_quantities(self.orderpoint, 3, 8)

    def test_semester_replenishment_with_customer_return(self):
        self.company.period_min_qty = 'semester'
        supplier_location = self.env.ref('stock.stock_location_suppliers')
        customer_location = self.env.ref('stock.stock_location_customers')
        self.create_validated_move(
            self.warehouse.in_type_id, supplier_location,
            self.warehouse.lot_stock_id, 10)
        self.create_validated_move(
            self.warehouse.out_type_id, self.warehouse.lot_stock_id,
            customer_location, 8)
        self.create_validated_move(
            self.warehouse.in_type_id, customer_location,
            self.warehouse.lot_stock_id, 3)
        self.assertEqual(self.orderpoint.qty_forecast, 5)
        self.assertEqual(self.orderpoint._get_historical_monthly_demand(), 1)
        self.orderpoint._compute_qty_to_order()
        self.assertEqual(self.orderpoint.qty_to_order, 0)
        self.assert_historical_quantities(self.orderpoint, 1, 5)

    def test_monthly_replenishment_rounds_to_multiple_quantity(self):
        self.company.period_min_qty = 'monthly'
        self.orderpoint.qty_multiple = 5
        supplier_location = self.env.ref('stock.stock_location_suppliers')
        customer_location = self.env.ref('stock.stock_location_customers')
        self.create_validated_move(
            self.warehouse.in_type_id, supplier_location,
            self.warehouse.lot_stock_id, 10)
        self.create_validated_move(
            self.warehouse.out_type_id, self.warehouse.lot_stock_id,
            customer_location, 8)
        self.orderpoint._compute_qty_to_order()
        self.assertEqual(self.orderpoint.qty_to_order, 10)
        self.assert_historical_quantities(self.orderpoint, 8, 8)

    def test_cancelled_sales_are_not_historical_demand(self):
        self.company.period_min_qty = 'monthly'
        customer_location = self.env.ref('stock.stock_location_customers')
        self.create_cancelled_move(
            self.warehouse.out_type_id, self.warehouse.lot_stock_id,
            customer_location, 8)
        self.assertEqual(
            self.orderpoint._get_historical_monthly_demand(), 0)
        self.orderpoint._compute_qty_to_order()
        self.assertEqual(self.orderpoint.qty_to_order, 0)
        self.assert_historical_quantities(self.orderpoint, 0, 0)

    def test_historical_demand_isolated_by_company(self):
        company_2 = self.env['res.company'].create({
            'name': 'Period demand company 2',
        })
        company_2.period_min_qty = 'monthly'
        warehouse_2 = self.env['stock.warehouse'].create({
            'name': 'Period demand warehouse 2',
            'code': 'PD2',
            'company_id': company_2.id,
        })
        orderpoint_2 = self.env[
            'stock.warehouse.orderpoint'].with_company(company_2).create({
                'warehouse_id': warehouse_2.id,
                'location_id': warehouse_2.lot_stock_id.id,
                'product_id': self.product.id,
                'product_min_qty': 0,
                'product_max_qty': 0,
            })
        customer_location = self.env.ref('stock.stock_location_customers')
        customer_location_2 = self.env['stock.location'].with_company(
            company_2).create({
                'name': 'Period demand customer 2',
                'usage': 'customer',
                'company_id': False,
            })
        self.create_validated_move(
            self.warehouse.out_type_id, self.warehouse.lot_stock_id,
            customer_location, 8)
        self.assertEqual(
            orderpoint_2._get_historical_monthly_demand(), 0)
        company_2_move = self.create_validated_move(
            warehouse_2.out_type_id, warehouse_2.lot_stock_id,
            customer_location_2, 3, company=company_2)
        self.assertEqual(company_2_move.company_id, company_2)
        self.assertEqual(
            orderpoint_2._get_historical_monthly_demand(), 3)
        self.assert_historical_quantities(self.orderpoint, 1, 8)
        self.assert_historical_quantities(orderpoint_2, 3, 3)

    def test_annual_without_deposit(self):
        self.company.period_min_qty = 'annual'
        customer_location = self.env.ref('stock.stock_location_customers')
        self.create_inventory(self.warehouse.lot_stock_id, 25)
        self.assertEqual(self.orderpoint.qty_on_hand, 25)
        self.create_validated_move(
            self.warehouse.out_type_id, self.warehouse.lot_stock_id,
            customer_location, 10)
        self.assertEqual(self.orderpoint.qty_on_hand, 15)
        self.create_validated_move(
            self.warehouse.in_type_id, customer_location,
            self.warehouse.lot_stock_id, 6)
        self.assertEqual(self.orderpoint.qty_on_hand, 21)
        self.assertEqual(
            self.orderpoint._get_historical_monthly_demand(), 0)
        self.orderpoint._compute_qty_to_order()
        self.assertEqual(self.orderpoint.qty_to_order, 0)
        self.assert_historical_quantities(self.orderpoint, 0, 4)

    def test_annual_with_deposit_sale_deposit_and_move_to_customer(self):
        self.company.period_min_qty = 'annual'
        customer_location = self.env.ref('stock.stock_location_customers')
        deposit_location = self.create_deposit_location()
        self.create_inventory(self.warehouse.lot_stock_id, 10)
        self.create_validated_move(
            self.warehouse.int_type_id, self.warehouse.lot_stock_id,
            deposit_location, 5)
        self.assertEqual(self.orderpoint.qty_on_hand, 5)
        self.assertEqual(
            self.orderpoint._get_historical_monthly_demand(), 0)
        self.create_validated_move(
            self.warehouse.out_type_id, deposit_location,
            customer_location, 2)
        self.assertEqual(self.orderpoint.qty_on_hand, 5)
        self.assertEqual(
            self.orderpoint._get_historical_monthly_demand(), 0)
        self.assert_historical_quantities(self.orderpoint, 0, 5)

    def test_annual_with_deposit_sale_and_return_to_stock(self):
        self.company.period_min_qty = 'annual'
        deposit_location = self.create_deposit_location()
        self.create_inventory(self.warehouse.lot_stock_id, 10)
        self.create_validated_move(
            self.warehouse.int_type_id, self.warehouse.lot_stock_id,
            deposit_location, 5)
        self.create_validated_move(
            self.warehouse.in_type_id, deposit_location,
            self.warehouse.lot_stock_id, 5)
        self.assertEqual(self.orderpoint.qty_on_hand, 10)
        self.assertEqual(
            self.orderpoint._get_historical_monthly_demand(), 0)
        self.assert_historical_quantities(self.orderpoint, 0, 0)

    def test_annual_with_and_without_deposit(self):
        self.company.period_min_qty = 'annual'
        customer_location = self.env.ref('stock.stock_location_customers')
        self.create_inventory(self.warehouse.lot_stock_id, 25)
        self.create_validated_move(
            self.warehouse.out_type_id, self.warehouse.lot_stock_id,
            customer_location, 10)
        self.create_validated_move(
            self.warehouse.in_type_id, customer_location,
            self.warehouse.lot_stock_id, 6)
        self.assertEqual(
            self.orderpoint._get_historical_monthly_demand(), 0)
        deposit_location = self.create_deposit_location()
        self.create_validated_move(
            self.warehouse.int_type_id, self.warehouse.lot_stock_id,
            deposit_location, 5)
        self.assertEqual(self.orderpoint.qty_on_hand, 16)
        self.assertEqual(
            self.orderpoint._get_historical_monthly_demand(), 1)
        self.assert_historical_quantities(self.orderpoint, 1, 9)

    def test_semester_without_deposit(self):
        self.company.period_min_qty = 'semester'
        customer_location = self.env.ref('stock.stock_location_customers')
        self.create_inventory(self.warehouse.lot_stock_id, 25)
        self.create_validated_move(
            self.warehouse.out_type_id, self.warehouse.lot_stock_id,
            customer_location, 10)
        self.assertEqual(
            self.orderpoint._get_historical_monthly_demand(), 2)
        self.create_validated_move(
            self.warehouse.in_type_id, customer_location,
            self.warehouse.lot_stock_id, 6)
        self.assertEqual(self.orderpoint.qty_on_hand, 21)
        self.assertEqual(
            self.orderpoint._get_historical_monthly_demand(), 1)
        self.assert_historical_quantities(self.orderpoint, 1, 4)

    def test_semester_with_deposit_sale_deposit_and_move_to_customer(self):
        self.company.period_min_qty = 'semester'
        customer_location = self.env.ref('stock.stock_location_customers')
        deposit_location = self.create_deposit_location()
        self.create_inventory(self.warehouse.lot_stock_id, 10)
        self.create_validated_move(
            self.warehouse.int_type_id, self.warehouse.lot_stock_id,
            deposit_location, 5)
        self.assertEqual(
            self.orderpoint._get_historical_monthly_demand(), 1)
        self.create_validated_move(
            self.warehouse.out_type_id, deposit_location,
            customer_location, 2)
        self.assertEqual(self.orderpoint.qty_on_hand, 5)
        self.assertEqual(
            self.orderpoint._get_historical_monthly_demand(), 1)
        self.assert_historical_quantities(self.orderpoint, 1, 5)

    def test_semester_with_deposit_sale_and_return_to_stock(self):
        self.company.period_min_qty = 'semester'
        deposit_location = self.create_deposit_location()
        self.create_inventory(self.warehouse.lot_stock_id, 10)
        self.create_validated_move(
            self.warehouse.int_type_id, self.warehouse.lot_stock_id,
            deposit_location, 5)
        self.create_validated_move(
            self.warehouse.in_type_id, deposit_location,
            self.warehouse.lot_stock_id, 5)
        self.assertEqual(self.orderpoint.qty_on_hand, 10)
        self.assertEqual(
            self.orderpoint._get_historical_monthly_demand(), 0)
        self.assert_historical_quantities(self.orderpoint, 0, 0)

    def test_semester_with_and_without_deposit(self):
        self.company.period_min_qty = 'semester'
        customer_location = self.env.ref('stock.stock_location_customers')
        self.create_inventory(self.warehouse.lot_stock_id, 25)
        self.create_validated_move(
            self.warehouse.out_type_id, self.warehouse.lot_stock_id,
            customer_location, 10)
        self.create_validated_move(
            self.warehouse.in_type_id, customer_location,
            self.warehouse.lot_stock_id, 6)
        self.assertEqual(
            self.orderpoint._get_historical_monthly_demand(), 1)
        deposit_location = self.create_deposit_location()
        self.create_validated_move(
            self.warehouse.int_type_id, self.warehouse.lot_stock_id,
            deposit_location, 5)
        self.assertEqual(self.orderpoint.qty_on_hand, 16)
        self.assertEqual(
            self.orderpoint._get_historical_monthly_demand(), 2)
        self.assert_historical_quantities(self.orderpoint, 2, 9)
