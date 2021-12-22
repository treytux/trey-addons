###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests import common


class TestPurchaseOrderSaleOrderLink(common.TransactionCase):

    def setUp(self):
        super().setUp()
        user_type_payable = self.env.ref('account.data_account_type_payable')
        account_account_obj = self.env['account.account']
        self.account_payable = account_account_obj.create({
            'code': 'NC1110',
            'name': 'Test payable account',
            'user_type_id': user_type_payable.id,
            'reconcile': True,
        })
        user_type_receivable = self.env.ref(
            'account.data_account_type_receivable')
        self.account_receivable = account_account_obj.create({
            'code': 'NC1111',
            'name': 'Test receivable account',
            'user_type_id': user_type_receivable.id,
            'reconcile': True,
        })
        self.partner = self.env['res.partner'].create({
            'name': 'Partner test',
            'email': 'customer@customer.com',
            'customer': True,
            'property_account_payable_id': self.account_payable.id,
            'property_account_receivable_id': self.account_receivable.id,
        })
        self.partner_vendor_service = self.env['res.partner'].create({
            'name': 'Service supplier',
            'email': 'supplier@supplier.com',
            'supplier': True,
        })
        uom_unit = self.env.ref('uom.product_uom_unit')
        self.buy_route = self.env.ref('purchase_stock.route_warehouse0_buy')
        self.mto_route = self.env.ref('stock.route_warehouse0_mto')
        user_type_income = self.env.ref(
            'account.data_account_type_direct_costs')
        self.product_purchase = account_account_obj.create({
            'code': 'INCOME_PROD_PURCHASE',
            'name': 'Icome - Test Account',
            'user_type_id': user_type_income.id,
        })
        self.product_category = self.env['product.category'].create({
            'name': 'Product category with income account',
            'property_account_income_categ_id': self.product_purchase.id,
        })
        self.product_order = self.env['product.product'].create({
            'name': 'Test product',
            'standard_price': 235,
            'list_price': 280,
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
        self.service_purchase_1 = self.env['product.product'].create({
            'name': 'Out-sourced service 1',
            'standard_price': 200,
            'list_price': 180,
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
        })
        self.supplierinfo1 = self.env['product.supplierinfo'].create({
            'name': self.partner_vendor_service.id,
            'price': 100,
            'product_tmpl_id': self.service_purchase_1.product_tmpl_id.id,
            'delay': 1,
        })
        self.service_purchase_2 = self.env['product.product'].create({
            'name': 'Out-sourced service 2',
            'standard_price': 20,
            'list_price': 15,
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
            'route_ids': [(6, 0, [self.mto_route.id])],
        })
        self.supplierinfo2 = self.env['product.supplierinfo'].create({
            'name': self.partner_vendor_service.id,
            'price': 10,
            'product_tmpl_id': self.service_purchase_2.product_tmpl_id.id,
            'delay': 5,
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
            'supplier': True,
        })
        self.customer_01 = self.env['res.partner'].create({
            'name': 'Customer test 1',
            'customer': True,
        })
        self.customer_02 = self.env['res.partner'].create({
            'name': 'Customer test 2',
            'customer': True,
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
            'name': self.customer_01.id,
            'product_tmpl_id': self.product_01.product_tmpl_id.id,
            'price': 80,
        })
        self.env['product.supplierinfo'].create({
            'name': self.customer_02.id,
            'product_tmpl_id': self.product_02.product_tmpl_id.id,
            'price': 8,
        })
        self.warehouse = self.env.ref('stock.warehouse0')
        self.env['stock.warehouse.orderpoint'].create({
            'warehouse_id': self.warehouse.id,
            'location_id': self.warehouse.lot_stock_id.id,
            'product_id': self.product_01.id,
            'product_min_qty': 25,
            'product_max_qty': 50,
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
                })
            ]
        })
        sale.action_confirm()
        purchase_order = self.env['purchase.order'].search([
            ('origin', 'ilike', sale.name)
        ])
        self.assertEquals(len(purchase_order), 1)
        self.assertEquals(len(purchase_order.order_line), 1)
        self.assertEquals(
            purchase_order.order_line[0].product_id.id, self.product_01.id)
        self.assertEquals(
            purchase_order.order_line[0].move_dest_ids[0].sale_line_id.id,
            sale.order_line[0].id)
        self.assertIn(sale.name, purchase_order.origin)
        self.assertEquals(purchase_order.sale_count, 1)

    def test_link_purchase_order_sale_order(self):
        self.sale_order_1.action_confirm()
        self.sale_order_2.action_confirm()
        purchase_order = self.env['purchase.order'].search([
            ('partner_id', '=', self.supplierinfo1.name.id),
            ('state', '=', 'draft'),
        ])
        self.assertEquals(len(purchase_order), 1)
        self.assertEquals(len(purchase_order.order_line), 1)
        self.assertIn(self.sale_order_2.name, purchase_order.origin)
        self.assertEquals(purchase_order.sale_count, 1)
        purchase_order = self.env['purchase.order'].search([
            ('partner_id', '=', self.supplierinfo2.name.id),
            ('state', '=', 'draft'),
        ])
        self.assertEquals(len(purchase_order), 1)
        self.assertEquals(len(purchase_order.order_line), 1)
        self.assertIn(self.sale_order_2.name, purchase_order.origin)
        self.assertEquals(purchase_order.sale_count, 1)

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
        sale_01.action_confirm()
        purchase_order_01 = self.env['purchase.order'].search([
            ('origin', 'ilike', sale_01.name),
        ])
        self.assertEquals(len(purchase_order_01), 1)
        self.assertEquals(len(purchase_order_01.order_line), 1)
        self.assertEquals(purchase_order_01.sale_count, 1)
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
        sale_02.action_confirm()
        purchase_order_02 = self.env['purchase.order'].search([
            ('origin', 'ilike', sale_02.name),
        ])
        self.assertEquals(len(purchase_order_02), 1)
        self.assertEquals(len(purchase_order_02.order_line), 1)
        self.assertEquals(purchase_order_02.sale_count, 1)
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
        sale_03.action_confirm()
        purchase_order_03 = self.env['purchase.order'].search([
            ('origin', 'ilike', sale_03.name),
        ])
        self.assertEquals(len(purchase_order_03), 2)
        self.assertEquals(len(purchase_order_01.order_line), 1)
        self.assertEquals(len(purchase_order_02.order_line), 1)
        self.assertEquals(purchase_order_03[0].sale_count, 2)
        self.assertEquals(purchase_order_03[1].sale_count, 2)
