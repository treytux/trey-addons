###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests import common


class TestSaleOrderPurchaseOrderLink(common.TransactionCase):

    def setUp(self):
        super().setUp()
        account_account = self.env['account.account']
        self.account_payable = account_account.create({
            'code': 'NC1110',
            'name': 'Test Payable Account',
            'account_type': 'liability_payable',
            'reconcile': True
        })
        self.account_receivable = account_account.create({
            'code': 'NC1111',
            'name': 'Test Receivable Account',
            'account_type': 'asset_receivable',
            'reconcile': True
        })
        self.partner = self.env['res.partner'].create({
            'name': 'Partner test',
            'email': 'customer@customer.com',
            'property_account_payable_id': self.account_payable.id,
            'property_account_receivable_id': self.account_receivable.id,
        })
        self.partner_vendor_service = self.env['res.partner'].create({
            'name': 'Service supplier',
            'email': 'supplier@supplier.com',
        })
        uom_unit = self.env.ref('uom.product_uom_unit')
        self.buy_route = self.env.ref('purchase_stock.route_warehouse0_buy')
        self.mto_route = self.env.ref('stock.route_warehouse0_mto')
        self.product_purchase = account_account.create({
            'code': 'INCOMEPRODPURCHASE',
            'name': 'Icome - Test Account',
            'account_type': 'income',
        })
        self.product_category = self.env['product.category'].create({
            'name': 'Product Category with income account',
            'property_account_income_categ_id': self.product_purchase.id
        })
        self.product_order = self.env['product.product'].create({
            'name': 'Test Product',
            'standard_price': 235.0,
            'list_price': 280.0,
            'type': 'consu',
            'uom_id': uom_unit.id,
            'uom_po_id': uom_unit.id,
            'invoice_policy': 'order',
            'expense_policy': 'no',
            'default_code': 'PROD_ORDER',
            'service_type': 'manual',
            'taxes_id': False,
            'categ_id': self.product_category.id,
        })
        self.service_purchase_1 = self.env['product.template'].create({
            'name': 'Out-sourced Service 1',
            'standard_price': 200.0,
            'list_price': 180.0,
            'type': 'service',
            'uom_id': uom_unit.id,
            'uom_po_id': uom_unit.id,
            'invoice_policy': 'delivery',
            'expense_policy': 'no',
            'default_code': 'SERV_DEL',
            'service_type': 'manual',
            'taxes_id': False,
            'categ_id': self.product_category.id,
            'service_to_purchase': True,
            'seller_ids': [
                (0, 0, {
                    'partner_id': self.partner_vendor_service.id,
                    'price': 100,
                })],
        })
        self.service_purchase_2 = self.env['product.product'].create({
            'name': 'Out-sourced Service 2',
            'standard_price': 20.0,
            'list_price': 15.0,
            'type': 'service',
            'uom_id': uom_unit.id,
            'uom_po_id': uom_unit.id,
            'invoice_policy': 'order',
            'expense_policy': 'no',
            'default_code': 'SERV_ORD',
            'service_type': 'manual',
            'taxes_id': False,
            'categ_id': self.product_category.id,
            'service_to_purchase': True,
            'seller_ids': [
                (0, 0, {
                    'partner_id': self.partner_vendor_service.id,
                    'price': 10,
                })],
            'route_ids': [(6, 0, [self.mto_route.id])],
        })
        self.sale_order_1 = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'partner_invoice_id': self.partner.id,
            'partner_shipping_id': self.partner.id,
        })
        self.order_line_product_order = self.env['sale.order.line'].create({
            'name': self.product_order.name,
            'product_id': self.product_order.id,
            'product_uom_qty': 2,
            'product_uom': self.product_order.uom_id.id,
            'price_unit': self.product_order.list_price,
            'order_id': self.sale_order_1.id,
            'tax_id': False,
        })
        self.sale_order_2 = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'partner_invoice_id': self.partner.id,
            'partner_shipping_id': self.partner.id,
        })
        self.sol2_service_purchase_2 = self.env['sale.order.line'].create({
            'name': self.service_purchase_2.name,
            'product_id': self.service_purchase_2.id,
            'product_uom_qty': 7,
            'product_uom': self.service_purchase_2.uom_id.id,
            'price_unit': self.service_purchase_2.list_price,
            'order_id': self.sale_order_2.id,
            'tax_id': False,
            'route_id': self.mto_route.id,
        })
        self.supplier = self.env['res.partner'].create({
            'name': 'Supplier test',
        })
        self.customer_01 = self.env['res.partner'].create({
            'name': 'Customer test 1',
        })
        self.customer_02 = self.env['res.partner'].create({
            'name': 'Customer test 2',
        })
        self.product_01 = self.env['product.product'].create({
            'type': 'product',
            'name': 'Product test 1',
            'standard_price': 10,
            'list_price': 100,
            'route_ids': [(6, 0, [self.buy_route.id, self.mto_route.id])],
        })
        self.product_02 = self.env['product.product'].create({
            'type': 'product',
            'name': 'Product test 2',
            'standard_price': 5,
            'list_price': 10,
            'route_ids': [(6, 0, [self.buy_route.id, self.mto_route.id])],
        })
        self.env['product.supplierinfo'].create({
            'partner_id': self.customer_01.id,
            'product_tmpl_id': self.product_01.product_tmpl_id.id,
            'price': 80,
        })
        self.env['product.supplierinfo'].create({
            'partner_id': self.customer_02.id,
            'product_tmpl_id': self.product_02.product_tmpl_id.id,
            'price': 8,
        })
        self.warehouse = self.env.ref('stock.warehouse0')
        self.env['stock.warehouse.orderpoint'].create({
            'warehouse_id': self.warehouse.id,
            'location_id': self.warehouse.lot_stock_id.id,
            'product_id': self.product_01.id,
            'product_min_qty': 25.00,
            'product_max_qty': 50.00,
        })

    def test_link_purchase_order_from_route_mto(self):
        sale = self.env['sale.order'].create({
            'partner_id': self.customer_01.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product_01.id,
                    'price_unit': self.product_01.list_price,
                    'product_uom_qty': 1,
                    'route_id': self.mto_route.id,
                }),
            ],
        })
        self.assertEqual(sale.purchase_count, 0)
        sale.action_confirm()
        self.assertEqual(sale.purchase_count, 1)
        purchase_order = self.env['purchase.order'].search([
            ('origin', 'ilike', sale.name),
        ])
        self.assertEqual(len(purchase_order), 1)
        self.assertEqual(len(purchase_order.order_line), 2)
        purchase_line_by_mto_rule = purchase_order.order_line.filtered(
            lambda ln: ln.product_uom_qty == 1)
        self.assertTrue(purchase_line_by_mto_rule)
        purchase_line_by_orderpoint = purchase_order.order_line.filtered(
            lambda ln: ln.product_uom_qty == 50)
        self.assertTrue(purchase_line_by_orderpoint)
        self.assertEqual(
            purchase_line_by_mto_rule.product_id.id, self.product_01.id)
        self.assertIn(sale.name, purchase_order.origin)
        self.assertEqual(len(purchase_line_by_mto_rule.move_dest_ids), 1)
        self.assertEqual(
            purchase_line_by_mto_rule.move_dest_ids[0].sale_line_id.id,
            sale.order_line[0].id)
        line = sale.order_line[0]
        moves = self.env['stock.move'].search([
            ('sale_line_id.id', '=', line.id),
        ])
        self.assertEqual(len(moves), 1)
        move = moves[0]
        purchase_lines = self.env['purchase.order.line'].search([
            ('move_dest_ids', 'in', move.id),
        ])
        self.assertEqual(len(purchase_lines), 1)
        purchase_line = purchase_lines[0]
        self.assertEqual(purchase_line.order_id.id, purchase_order.id)
        self.assertFalse(purchase_line_by_mto_rule.sale_line_id)
        self.assertFalse(purchase_line_by_mto_rule.sale_order_id)
        self.assertEqual(
            purchase_line_by_orderpoint.product_id.id, self.product_01.id)
        self.assertIn(sale.name, purchase_order.origin)
        self.assertIn('OP', purchase_order.origin)
        self.assertFalse(purchase_line_by_orderpoint.move_dest_ids)

    def test_link_sale_order_purchase_order(self):
        self.assertEqual(self.sale_order_1.purchase_count, 0)
        self.assertEqual(self.sale_order_2.purchase_count, 0)
        self.sale_order_1.action_confirm()
        self.sale_order_2.action_confirm()
        self.assertEqual(self.sale_order_1.purchase_count, 0)
        self.assertEqual(self.sale_order_2.purchase_count, 1)
        self.supplierinfo1 = self.service_purchase_1.seller_ids[0]
        purchase_order = self.env['purchase.order'].search([
            ('partner_id', '=', self.supplierinfo1.partner_id.id),
            ('state', '=', 'draft'),
        ])
        self.assertEqual(len(purchase_order), 1)
        self.assertEqual(len(purchase_order.order_line), 1)
        self.assertEqual(
            purchase_order.order_line[0].product_id.id,
            self.service_purchase_2.id)
        self.assertIn(self.sale_order_2.name, purchase_order.origin)
        self.assertEqual(
            purchase_order.order_line[0].sale_line_id.id,
            self.sale_order_2.order_line[0].id)
        self.assertEqual(
            purchase_order.order_line[0].sale_order_id.id,
            self.sale_order_2.id)
        line = self.sale_order_2.order_line[0]
        moves = self.env['stock.move'].search([
            ('sale_line_id.id', '=', line.id),
        ])
        self.assertEqual(len(moves), 0)

    def test_multiple_case_3(self):
        sale_01 = self.env['sale.order'].create({
            'partner_id': self.customer_01.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product_01.id,
                    'price_unit': self.product_01.list_price,
                    'product_uom_qty': 1,
                    'route_id': self.mto_route.id,
                }),
            ],
        })
        self.assertEqual(sale_01.purchase_count, 0)
        sale_01.action_confirm()
        self.assertEqual(sale_01.purchase_count, 1)
        purchase_order_01 = self.env['purchase.order'].search([
            ('origin', 'ilike', sale_01.name),
        ])
        self.assertEqual(len(purchase_order_01), 1)
        self.assertEqual(len(purchase_order_01.order_line), 2)
        purchase_line_01_by_mto_rule = purchase_order_01.order_line.filtered(
            lambda ln: ln.product_uom_qty == 1)
        self.assertTrue(purchase_line_01_by_mto_rule)
        purchase_line_01_by_procurement = purchase_order_01.order_line.filtered(
            lambda ln: ln.product_uom_qty == 50)
        self.assertTrue(purchase_line_01_by_procurement)
        sale_02 = self.env['sale.order'].create({
            'partner_id': self.customer_02.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product_02.id,
                    'price_unit': self.product_02.list_price,
                    'product_uom_qty': 1,
                    'route_id': self.mto_route.id,
                }),
            ],
        })
        self.assertEqual(sale_02.purchase_count, 0)
        sale_02.action_confirm()
        self.assertEqual(sale_02.purchase_count, 1)
        purchase_order_02 = self.env['purchase.order'].search([
            ('origin', 'ilike', sale_02.name),
        ])
        self.assertEqual(len(purchase_order_02), 1)
        self.assertEqual(len(purchase_order_02.order_line), 1)
        sale_03 = self.env['sale.order'].create({
            'partner_id': self.customer_01.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product_01.id,
                    'price_unit': self.product_01.list_price,
                    'product_uom_qty': 1,
                    'route_id': self.mto_route.id,
                }),
                (0, 0, {
                    'product_id': self.product_02.id,
                    'price_unit': self.product_02.list_price,
                    'product_uom_qty': 1,
                    'route_id': self.mto_route.id,
                }),
            ],
        })
        self.assertEqual(sale_03.purchase_count, 0)
        sale_03.action_confirm()
        self.assertEqual(sale_03.purchase_count, 2)
        purchase_order_03 = self.env['purchase.order'].search([
            ('origin', 'ilike', sale_03.name),
        ])
        self.assertEqual(len(purchase_order_03), 2)
        self.assertEqual(len(purchase_order_02.order_line), 1)
        self.assertFalse(purchase_line_01_by_mto_rule.sale_line_id)
        self.assertFalse(purchase_order_02.order_line[0].sale_line_id)
        self.assertFalse(purchase_line_01_by_mto_rule.sale_order_id)
        self.assertFalse(purchase_order_02.order_line[0].sale_order_id)
        self.assertIn(
            sale_03.order_line[0].id,
            purchase_line_01_by_mto_rule.move_dest_ids.mapped(
                'sale_line_id').ids)
        self.assertIn(
            sale_03.order_line[1].id,
            purchase_order_02.order_line.move_dest_ids.mapped(
                'sale_line_id').ids)
