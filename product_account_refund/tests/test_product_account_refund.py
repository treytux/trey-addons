###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields
from odoo.tests import common


class TestProductAccountRefund(common.TransactionCase):
    def setUp(self):
        super().setUp()
        self.partner = self.env.ref('base.res_partner_3')
        self.product = self.env.ref(
            'product.product_product_3_product_template').product_variant_id
        self.inventory(9999)
        self.assertFalse(self.product.property_account_sales_refund_id)
        self.assertFalse(self.product.property_account_purchase_refund_id)
        self.assertFalse(
            self.product.categ_id.property_account_sales_refund_id)
        self.assertFalse(
            self.product.categ_id.property_account_purchase_refund_id)
        type_revenue = self.env.ref('account.data_account_type_revenue')
        type_payable = self.env.ref('account.data_account_type_payable')
        self.account_sale_test = self.env['account.account'].create({
            'name': 'Sale test',
            'code': 'XX_708',
            'user_type_id': type_revenue.id,
            'reconcile': True,
        })
        self.account_customer_test = self.env['account.account'].create({
            'name': 'Customer test',
            'code': 'XX_608',
            'user_type_id': type_payable.id,
            'reconcile': True,
        })

    def tearDown(self):
        super().tearDown()
        self.inventory(0)

    def inventory(self, qty):
        location = self.env.ref('stock.stock_location_stock')
        inventory = self.env['stock.inventory'].create({
            'name': 'add products for tests',
            'filter': 'product',
            'location_id': location.id,
            'product_id': self.product.id,
            'exhausted': True,
        })
        inventory.action_start()
        stock_loc = self.env.ref('stock.stock_location_stock')
        inventory.line_ids.write({
            'product_qty': qty,
            'location_id': stock_loc.id,
        })
        inventory._action_done()

    def test_create_invoice_from_sale_order_01(self):
        product = self.env['product.product'].create({
            'type': 'product',
            'company_id': False,
            'name': 'Product test 3',
            'standard_price': 10,
            'list_price': 100,
        })
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': product.id,
                    'price_unit': 40,
                    'product_uom_qty': 1,
                }),
            ],
        })
        sale.action_confirm()
        sale.action_invoice_create()
        invoice = sale.invoice_ids[0]
        invoice.action_invoice_open()
        self.env['account.invoice.refund'].with_context(
            active_ids=invoice.ids).create({
                'filter_refund': 'refund',
                'description': 'Refund season',
            }).invoice_refund()
        refund = invoice.refund_invoice_ids[0]
        self.assertEqual(len(refund.invoice_line_ids), 1)
        refund_line_01 = refund.invoice_line_ids[0]
        self.assertTrue(refund_line_01.account_id)
        self.assertFalse(product.property_account_sales_refund_id)
        self.assertFalse(product.categ_id.property_account_sales_refund_id)
        self.assertNotEqual(
            refund_line_01.account_id,
            product.property_account_sales_refund_id)
        self.assertNotEqual(
            refund_line_01.account_id,
            product.categ_id.property_account_sales_refund_id)
        self.assertNotEqual(
            refund_line_01.account_id, self.account_sale_test)

    def test_create_invoice_from_sale_order_02(self):
        product = self.env['product.product'].create({
            'type': 'product',
            'company_id': False,
            'name': 'Product test 3',
            'standard_price': 10,
            'list_price': 100,
        })
        product.property_account_sales_refund_id = (
            self.account_sale_test)
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': product.id,
                    'price_unit': 40,
                    'product_uom_qty': 1,
                }),
            ],
        })
        sale.action_confirm()
        sale.action_invoice_create()
        invoice = sale.invoice_ids[0]
        invoice.action_invoice_open()
        self.env['account.invoice.refund'].with_context(
            active_ids=invoice.ids).create({
                'filter_refund': 'refund',
                'description': 'Refund season',
            }).invoice_refund()
        refund = invoice.refund_invoice_ids[0]
        self.assertEqual(len(refund.invoice_line_ids), 1)
        refund_line_01 = refund.invoice_line_ids[0]
        self.assertEqual(
            refund_line_01.account_id,
            product.property_account_sales_refund_id)
        self.assertFalse(refund.move_id)
        refund.action_invoice_open()
        self.assertTrue(refund.move_id)
        move_account = refund.move_id.line_ids.filtered(
            lambda ln:
            ln.account_id == product.property_account_sales_refund_id)
        self.assertEqual(len(move_account), 1)

    def test_create_invoice_from_sale_order_03(self):
        product = self.env['product.product'].create({
            'type': 'product',
            'company_id': False,
            'name': 'Product test 3',
            'standard_price': 10,
            'list_price': 100,
        })
        product.categ_id.property_account_sales_refund_id = (
            self.account_sale_test)
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': product.id,
                    'price_unit': 40,
                    'product_uom_qty': 1,
                }),
            ],
        })
        sale.action_confirm()
        sale.action_invoice_create()
        invoice = sale.invoice_ids[0]
        invoice.action_invoice_open()
        self.env['account.invoice.refund'].with_context(
            active_ids=invoice.ids).create({
                'filter_refund': 'refund',
                'description': 'Refund season',
            }).invoice_refund()
        refund = invoice.refund_invoice_ids[0]
        self.assertEqual(len(refund.invoice_line_ids), 1)
        refund_line_01 = refund.invoice_line_ids[0]
        self.assertEqual(
            refund_line_01.account_id,
            product.categ_id.property_account_sales_refund_id)

    def test_create_invoice_from_sale_order_04(self):
        product = self.env['product.product'].create({
            'type': 'product',
            'company_id': False,
            'name': 'Product test 3',
            'standard_price': 10,
            'list_price': 100,
        })
        product.property_account_sales_refund_id = (
            self.account_sale_test)
        product.categ_id.property_account_sales_refund_id = (
            self.account_customer_test)
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': product.id,
                    'price_unit': 40,
                    'product_uom_qty': 1,
                }),
            ],
        })
        sale.action_confirm()
        sale.action_invoice_create()
        invoice = sale.invoice_ids[0]
        invoice.action_invoice_open()
        self.env['account.invoice.refund'].with_context(
            active_ids=invoice.ids).create({
                'filter_refund': 'refund',
                'description': 'Refund season',
            }).invoice_refund()
        refund = invoice.refund_invoice_ids[0]
        self.assertEqual(len(refund.invoice_line_ids), 1)
        refund_line_01 = refund.invoice_line_ids[0]
        self.assertEqual(
            refund_line_01.account_id,
            product.property_account_sales_refund_id)

    def test_create_invoice_from_purchase_order_01(self):
        product = self.env['product.product'].create({
            'type': 'product',
            'company_id': False,
            'name': 'Product test 4',
            'standard_price': 10,
            'list_price': 100,
        })
        purchase = self.env['purchase.order'].create({
            'partner_id': self.partner.id,
        })
        line_obj = self.env['purchase.order.line']
        line = line_obj.new({
            'order_id': purchase.id,
            'product_id': product.id,
            'price_unit': 100,
            'quantity': 1,
        })
        line.onchange_product_id()
        line_obj.create(line_obj._convert_to_write(line._cache))
        purchase.button_confirm()
        self.assertEqual(len(purchase.picking_ids), 1)
        picking = purchase.picking_ids[0]
        picking.action_confirm()
        picking.action_assign()
        for move in picking.move_lines:
            move.quantity_done = move.product_uom_qty
        picking.action_done()
        wizard_01 = self.env['purchase.order.invoice'].with_context({
            'active_id': purchase.id,
            'active_ids': purchase.ids,
            'active_model': 'purchase.order',
        }).create({
            'method': 'received',
        })
        self.assertEqual(len(purchase.invoice_ids), 0)
        wizard_01.action_invoice()
        self.assertEqual(len(purchase.invoice_ids), 1)
        invoice = purchase.invoice_ids[0]
        invoice.action_invoice_open()
        self.assertEquals(purchase.invoice_ids, invoice)
        self.assertEquals(len(purchase.invoice_ids), 1)
        self.env['account.invoice.refund'].with_context(
            active_ids=invoice.ids).create({
                'filter_refund': 'refund',
                'description': 'Refund season',
            }).invoice_refund()
        refund = invoice.refund_invoice_ids[0]
        refund_line_01 = refund.invoice_line_ids[0]
        self.assertNotEqual(
            refund_line_01.account_id,
            product.property_account_purchase_refund_id)
        self.assertNotEqual(
            refund_line_01.account_id,
            product.categ_id.property_account_purchase_refund_id)

    def test_create_invoice_from_purchase_order_02(self):
        product = self.env['product.product'].create({
            'type': 'product',
            'company_id': False,
            'name': 'Product test 4',
            'standard_price': 10,
            'list_price': 100,
        })
        product.property_account_purchase_refund_id = (
            self.account_sale_test)
        purchase = self.env['purchase.order'].create({
            'partner_id': self.partner.id,
        })
        line_obj = self.env['purchase.order.line']
        line = line_obj.new({
            'order_id': purchase.id,
            'product_id': product.id,
            'price_unit': 100,
            'quantity': 1,
        })
        line.onchange_product_id()
        line_obj.create(line_obj._convert_to_write(line._cache))
        purchase.button_confirm()
        self.assertEqual(len(purchase.picking_ids), 1)
        picking = purchase.picking_ids[0]
        picking.action_confirm()
        picking.action_assign()
        for move in picking.move_lines:
            move.quantity_done = move.product_uom_qty
        picking.action_done()
        wizard_01 = self.env['purchase.order.invoice'].with_context({
            'active_id': purchase.id,
            'active_ids': purchase.ids,
            'active_model': 'purchase.order',
        }).create({
            'method': 'received',
        })
        self.assertEqual(len(purchase.invoice_ids), 0)
        wizard_01.action_invoice()
        self.assertEqual(len(purchase.invoice_ids), 1)
        invoice = purchase.invoice_ids[0]
        invoice.action_invoice_open()
        self.assertEquals(purchase.invoice_ids, invoice)
        self.assertEquals(len(purchase.invoice_ids), 1)
        self.env['account.invoice.refund'].with_context(
            active_ids=invoice.ids).create({
                'filter_refund': 'refund',
                'description': 'Refund season',
            }).invoice_refund()
        refund = invoice.refund_invoice_ids[0]
        refund_line_01 = refund.invoice_line_ids[0]
        self.assertEqual(
            refund_line_01.account_id,
            product.property_account_purchase_refund_id)

    def test_create_invoice_from_purchase_order_03(self):
        product = self.env['product.product'].create({
            'type': 'product',
            'company_id': False,
            'name': 'Product test 4',
            'standard_price': 10,
            'list_price': 100,
        })
        product.categ_id.property_account_purchase_refund_id = (
            self.account_sale_test)
        purchase = self.env['purchase.order'].create({
            'partner_id': self.partner.id,
        })
        line_obj = self.env['purchase.order.line']
        line = line_obj.new({
            'order_id': purchase.id,
            'product_id': product.id,
            'price_unit': 100,
            'quantity': 1,
        })
        line.onchange_product_id()
        line_obj.create(line_obj._convert_to_write(line._cache))
        purchase.button_confirm()
        self.assertEqual(len(purchase.picking_ids), 1)
        picking = purchase.picking_ids[0]
        picking.action_confirm()
        picking.action_assign()
        for move in picking.move_lines:
            move.quantity_done = move.product_uom_qty
        picking.action_done()
        wizard_01 = self.env['purchase.order.invoice'].with_context({
            'active_id': purchase.id,
            'active_ids': purchase.ids,
            'active_model': 'purchase.order',
        }).create({
            'method': 'received',
        })
        self.assertEqual(len(purchase.invoice_ids), 0)
        wizard_01.action_invoice()
        self.assertEqual(len(purchase.invoice_ids), 1)
        invoice = purchase.invoice_ids[0]
        invoice.action_invoice_open()
        self.assertEquals(purchase.invoice_ids, invoice)
        self.assertEquals(len(purchase.invoice_ids), 1)
        self.env['account.invoice.refund'].with_context(
            active_ids=invoice.ids).create({
                'filter_refund': 'refund',
                'description': 'Refund season',
            }).invoice_refund()
        refund = invoice.refund_invoice_ids[0]
        refund_line_01 = refund.invoice_line_ids[0]
        self.assertEqual(
            refund_line_01.account_id,
            product.categ_id.property_account_purchase_refund_id)

    def test_create_invoice_from_purchase_order_04(self):
        product = self.env['product.product'].create({
            'type': 'product',
            'company_id': False,
            'name': 'Product test 4',
            'standard_price': 10,
            'list_price': 100,
        })
        product.property_account_purchase_refund_id = (
            self.account_sale_test)
        product.categ_id.property_account_purchase_refund_id = (
            self.account_customer_test)
        purchase = self.env['purchase.order'].create({
            'partner_id': self.partner.id,
        })
        line_obj = self.env['purchase.order.line']
        line = line_obj.new({
            'order_id': purchase.id,
            'product_id': product.id,
            'price_unit': 100,
            'quantity': 1,
        })
        line.onchange_product_id()
        line_obj.create(line_obj._convert_to_write(line._cache))
        purchase.button_confirm()
        self.assertEqual(len(purchase.picking_ids), 1)
        picking = purchase.picking_ids[0]
        picking.action_confirm()
        picking.action_assign()
        for move in picking.move_lines:
            move.quantity_done = move.product_uom_qty
        picking.action_done()
        wizard_01 = self.env['purchase.order.invoice'].with_context({
            'active_id': purchase.id,
            'active_ids': purchase.ids,
            'active_model': 'purchase.order',
        }).create({
            'method': 'received',
        })
        self.assertEqual(len(purchase.invoice_ids), 0)
        wizard_01.action_invoice()
        self.assertEqual(len(purchase.invoice_ids), 1)
        invoice = purchase.invoice_ids[0]
        invoice.action_invoice_open()
        self.assertEquals(purchase.invoice_ids, invoice)
        self.assertEquals(len(purchase.invoice_ids), 1)
        self.env['account.invoice.refund'].with_context(
            active_ids=invoice.ids).create({
                'filter_refund': 'refund',
                'description': 'Refund season',
            }).invoice_refund()
        refund = invoice.refund_invoice_ids[0]
        refund_line_01 = refund.invoice_line_ids[0]
        self.assertEqual(
            refund_line_01.account_id,
            product.property_account_purchase_refund_id)

    def test_create_invoice_direct_01(self):
        default_line_account = self.env['account.account'].search([
            ('internal_type', '=', 'other'),
            ('deprecated', '=', False),
            ('company_id', '=', self.env.user.company_id.id),
        ], limit=1)
        invoice_lines = [
            (0, False, {
                'name': 'Account line test 1',
                'account_id': default_line_account.id,
                'product_id': self.product.id,
                'quantity': 1.0,
                'price_unit': 10.0,
            }),
            (0, False, {
                'name': 'Account line test 2',
                'account_id': default_line_account.id,
                'product_id': self.product.id,
                'quantity': 2.0,
                'price_unit': 15.0,
            }),
        ]
        invoice = self.env['account.invoice'].create({
            'partner_id': self.partner.id,
            'type': 'out_invoice',
            'invoice_line_ids': invoice_lines,
        })
        invoice.action_invoice_open()
        self.env['account.invoice.refund'].with_context(
            active_ids=invoice.ids).create({
                'filter_refund': 'refund',
                'description': 'Refund season',
            }).invoice_refund()
        refund = invoice.refund_invoice_ids[0]
        self.assertEqual(len(refund.invoice_line_ids), 2)
        refund_line_01 = refund.invoice_line_ids[0]
        refund_line_02 = refund.invoice_line_ids[1]
        self.assertEqual(refund_line_01.account_id, default_line_account)
        self.assertEqual(refund_line_02.account_id, default_line_account)

    def test_create_invoice_direct_02(self):
        self.product.property_account_sales_refund_id = (
            self.account_sale_test)
        self.assertTrue(self.product.property_account_sales_refund_id)
        self.assertFalse(
            self.product.categ_id.property_account_sales_refund_id)
        default_line_account = self.env['account.account'].search([
            ('internal_type', '=', 'other'),
            ('deprecated', '=', False),
            ('company_id', '=', self.env.user.company_id.id),
        ], limit=1)
        invoice_lines = [
            (0, False, {
                'name': 'Account line test 1',
                'account_id': default_line_account.id,
                'product_id': self.product.id,
                'quantity': 1.0,
                'price_unit': 10.0,
            }),
            (0, False, {
                'name': 'Account line test 2',
                'account_id': default_line_account.id,
                'product_id': self.product.id,
                'quantity': 2.0,
                'price_unit': 15.0,
            }),
        ]
        invoice = self.env['account.invoice'].create({
            'partner_id': self.partner.id,
            'type': 'out_invoice',
            'invoice_line_ids': invoice_lines,
        })
        invoice.action_invoice_open()
        self.env['account.invoice.refund'].with_context(
            active_ids=invoice.ids).create({
                'filter_refund': 'refund',
                'description': 'Refund season',
            }).invoice_refund()
        refund = invoice.refund_invoice_ids[0]
        self.assertEqual(refund.type, 'out_refund')
        self.assertEqual(len(refund.invoice_line_ids), 2)
        refund_line_01 = refund.invoice_line_ids[0]
        refund_line_02 = refund.invoice_line_ids[1]
        self.assertNotEqual(refund_line_01.account_id, default_line_account)
        self.assertNotEqual(refund_line_02.account_id, default_line_account)
        self.assertEqual(
            refund_line_01.account_id,
            self.product.property_account_sales_refund_id)
        self.assertEqual(
            refund_line_02.account_id,
            self.product.property_account_sales_refund_id)

    def test_create_invoice_direct_03(self):
        self.product.categ_id.property_account_sales_refund_id = (
            self.account_sale_test)
        self.assertTrue(
            self.product.categ_id.property_account_sales_refund_id)
        self.assertFalse(self.product.property_account_sales_refund_id)
        default_line_account = self.env['account.account'].search([
            ('internal_type', '=', 'other'),
            ('deprecated', '=', False),
            ('company_id', '=', self.env.user.company_id.id),
        ], limit=1)
        invoice_lines = [
            (0, False, {
                'name': 'Account line test 1',
                'account_id': default_line_account.id,
                'product_id': self.product.id,
                'quantity': 1.0,
                'price_unit': 10.0,
            }),
            (0, False, {
                'name': 'Account line test 2',
                'account_id': default_line_account.id,
                'product_id': self.product.id,
                'quantity': 2.0,
                'price_unit': 15.0,
            }),
        ]
        invoice = self.env['account.invoice'].create({
            'partner_id': self.partner.id,
            'type': 'out_invoice',
            'invoice_line_ids': invoice_lines,
        })
        invoice.action_invoice_open()
        self.env['account.invoice.refund'].with_context(
            active_ids=invoice.ids).create({
                'filter_refund': 'refund',
                'description': 'Refund season',
            }).invoice_refund()
        refund = invoice.refund_invoice_ids[0]
        self.assertEqual(refund.type, 'out_refund')
        self.assertEqual(len(refund.invoice_line_ids), 2)
        refund_line_01 = refund.invoice_line_ids[0]
        refund_line_02 = refund.invoice_line_ids[1]
        self.assertNotEqual(refund_line_01.account_id, default_line_account)
        self.assertNotEqual(refund_line_02.account_id, default_line_account)
        self.assertEqual(
            refund_line_01.account_id,
            self.product.categ_id.property_account_sales_refund_id)
        self.assertEqual(
            refund_line_02.account_id,
            self.product.categ_id.property_account_sales_refund_id)

    def test_create_invoice_direct_04(self):
        default_line_account = self.env['account.account'].search([
            ('internal_type', '=', 'other'),
            ('deprecated', '=', False),
            ('company_id', '=', self.env.user.company_id.id),
        ], limit=1)
        invoice_lines = [
            (0, False, {
                'name': 'Account line test 1',
                'account_id': default_line_account.id,
                'product_id': self.product.id,
                'quantity': 1.0,
                'price_unit': 10.0,
            }),
            (0, False, {
                'name': 'Account line test 2',
                'account_id': default_line_account.id,
                'product_id': self.product.id,
                'quantity': 2.0,
                'price_unit': 15.0,
            }),
        ]
        invoice = self.env['account.invoice'].create({
            'partner_id': self.partner.id,
            'type': 'in_invoice',
            'invoice_line_ids': invoice_lines,
        })
        invoice.action_invoice_open()
        self.env['account.invoice.refund'].with_context(
            active_ids=invoice.ids).create({
                'filter_refund': 'refund',
                'description': 'Refund season',
            }).invoice_refund()
        refund = invoice.refund_invoice_ids[0]
        self.assertEqual(refund.type, 'in_refund')
        self.assertEqual(len(refund.invoice_line_ids), 2)
        refund_line_01 = refund.invoice_line_ids[0]
        refund_line_02 = refund.invoice_line_ids[1]
        self.assertEqual(refund_line_01.account_id, default_line_account)
        self.assertEqual(refund_line_02.account_id, default_line_account)

    def test_create_invoice_direct_05(self):
        self.product.property_account_purchase_refund_id = (
            self.account_sale_test)
        self.assertTrue(self.product.property_account_purchase_refund_id)
        self.assertFalse(
            self.product.categ_id.property_account_purchase_refund_id)
        default_line_account = self.env['account.account'].search([
            ('internal_type', '=', 'other'),
            ('deprecated', '=', False),
            ('company_id', '=', self.env.user.company_id.id),
        ], limit=1)
        invoice_lines = [
            (0, False, {
                'name': 'Account line test 1',
                'account_id': default_line_account.id,
                'product_id': self.product.id,
                'quantity': 1.0,
                'price_unit': 10.0,
            }),
            (0, False, {
                'name': 'Account line test 2',
                'account_id': default_line_account.id,
                'product_id': self.product.id,
                'quantity': 2.0,
                'price_unit': 15.0,
            }),
        ]
        invoice = self.env['account.invoice'].create({
            'partner_id': self.partner.id,
            'type': 'in_invoice',
            'invoice_line_ids': invoice_lines,
        })
        invoice.action_invoice_open()
        self.env['account.invoice.refund'].with_context(
            active_ids=invoice.ids).create({
                'filter_refund': 'refund',
                'description': 'Refund season',
            }).invoice_refund()
        refund = invoice.refund_invoice_ids[0]
        self.assertEqual(refund.type, 'in_refund')
        self.assertEqual(len(refund.invoice_line_ids), 2)
        refund_line_01 = refund.invoice_line_ids[0]
        refund_line_02 = refund.invoice_line_ids[1]
        self.assertNotEqual(refund_line_01.account_id, default_line_account)
        self.assertNotEqual(refund_line_02.account_id, default_line_account)
        self.assertEqual(
            refund_line_01.account_id,
            self.product.property_account_purchase_refund_id)
        self.assertEqual(
            refund_line_02.account_id,
            self.product.property_account_purchase_refund_id)

    def test_create_invoice_direct_06(self):
        self.product.categ_id.property_account_purchase_refund_id = (
            self.account_sale_test)
        self.assertTrue(
            self.product.categ_id.property_account_purchase_refund_id)
        self.assertFalse(
            self.product.property_account_purchase_refund_id)
        default_line_account = self.env['account.account'].search([
            ('internal_type', '=', 'other'),
            ('deprecated', '=', False),
            ('company_id', '=', self.env.user.company_id.id),
        ], limit=1)
        invoice_lines = [
            (0, False, {
                'name': 'Account line test 1',
                'account_id': default_line_account.id,
                'product_id': self.product.id,
                'quantity': 1.0,
                'price_unit': 10.0,
            }),
            (0, False, {
                'name': 'Account line test 2',
                'account_id': default_line_account.id,
                'product_id': self.product.id,
                'quantity': 2.0,
                'price_unit': 15.0,
            }),
        ]
        invoice = self.env['account.invoice'].create({
            'partner_id': self.partner.id,
            'type': 'in_invoice',
            'invoice_line_ids': invoice_lines,
        })
        invoice.action_invoice_open()
        self.env['account.invoice.refund'].with_context(
            active_ids=invoice.ids).create({
                'filter_refund': 'refund',
                'description': 'Refund season',
            }).invoice_refund()
        refund = invoice.refund_invoice_ids[0]
        self.assertEqual(refund.type, 'in_refund')
        self.assertEqual(len(refund.invoice_line_ids), 2)
        refund_line_01 = refund.invoice_line_ids[0]
        refund_line_02 = refund.invoice_line_ids[1]
        self.assertNotEqual(refund_line_01.account_id, default_line_account)
        self.assertNotEqual(refund_line_02.account_id, default_line_account)
        self.assertEqual(
            refund_line_01.account_id,
            self.product.categ_id.property_account_purchase_refund_id)
        self.assertEqual(
            refund_line_02.account_id,
            self.product.categ_id.property_account_purchase_refund_id)

    def test_create_invoice_onchange_line(self):
        product_02 = self.env['product.product'].create({
            'type': 'product',
            'company_id': False,
            'name': 'Test product 2',
            'standard_price': 10,
            'list_price': 100,
        })
        self.product.property_account_purchase_refund_id = (
            self.account_sale_test)
        self.assertTrue(
            self.product.property_account_purchase_refund_id)
        self.assertFalse(
            self.product.categ_id.property_account_purchase_refund_id)
        default_line_account = self.env['account.account'].search([
            ('internal_type', '=', 'other'),
            ('deprecated', '=', False),
            ('company_id', '=', self.env.user.company_id.id),
        ], limit=1)
        invoice_lines = [
            (0, False, {
                'name': 'Account line test 1',
                'account_id': default_line_account.id,
                'product_id': product_02.id,
                'quantity': 1.0,
                'price_unit': 10.0,
            }),
            (0, False, {
                'name': 'Account line test 2',
                'account_id': default_line_account.id,
                'product_id': product_02.id,
                'quantity': 2.0,
                'price_unit': 15.0,
            }),
        ]
        invoice = self.env['account.invoice'].create({
            'partner_id': self.partner.id,
            'type': 'in_invoice',
            'invoice_line_ids': invoice_lines,
        })
        invoice.action_invoice_open()
        self.env['account.invoice.refund'].with_context(
            active_ids=invoice.ids).create({
                'filter_refund': 'refund',
                'description': 'Refund season',
            }).invoice_refund()
        refund = invoice.refund_invoice_ids[0]
        self.assertEqual(refund.type, 'in_refund')
        self.assertEqual(len(refund.invoice_line_ids), 2)
        refund_line_01 = refund.invoice_line_ids[0]
        refund_line_02 = refund.invoice_line_ids[1]
        self.assertEqual(refund_line_01.account_id, default_line_account)
        self.assertEqual(refund_line_02.account_id, default_line_account)
        refund_line_01.product_id = self.product.id
        refund_line_02.product_id = self.product.id
        refund_line_01._onchange_product_id()
        refund_line_02._onchange_product_id()
        self.assertNotEqual(refund_line_01.account_id, default_line_account)
        self.assertNotEqual(refund_line_02.account_id, default_line_account)
        self.assertEqual(
            refund_line_01.account_id,
            self.product.property_account_purchase_refund_id)
        self.assertEqual(
            refund_line_02.account_id,
            self.product.property_account_purchase_refund_id)

    def test_sale_advance_invoice_wizard_01(self):
        product = self.env['product.product'].create({
            'type': 'product',
            'company_id': False,
            'name': 'Product test 3',
            'standard_price': 10,
            'list_price': 100,
        })
        self.assertTrue(product.categ_id.property_account_income_categ_id)
        default_account = (
            product.categ_id.property_account_income_categ_id)
        product.invoice_policy = 'delivery'
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': product.id,
                    'price_unit': 100,
                    'product_uom_qty': 1,
                }),
            ],
        })
        sale.action_confirm()
        self.assertEqual(len(sale.picking_ids), 1)
        picking = sale.picking_ids[0]
        picking.action_confirm()
        picking.action_assign()
        for move in picking.move_lines:
            move.quantity_done = move.product_uom_qty
        picking.action_done()
        self.assertEqual(picking.state, 'done')
        ctx = {
            'tracking_disable': True,
            'mail_notrack': True,
            'mail_create_nolog': True,
            'active_model': 'sale.order',
            'active_ids': sale.ids,
            'active_id': sale.id,
        }
        wizard = self.env['sale.advance.payment.inv'].with_context(ctx).create(
            {'advance_payment_method': 'all'})
        wizard.create_invoices()
        self.assertEqual(len(sale.invoice_ids), 1)
        return_picking = self.env['stock.return.picking'].with_context(
            active_ids=picking.ids,
            active_id=picking.id,
        ).create({})
        return_picking.product_return_moves.write({
            'quantity': 1,
            'to_refund': True,
        })
        return_picking.create_returns()
        self.assertEqual(len(sale.picking_ids), 2)
        picking_ret = sale.picking_ids.filtered(
            lambda p: p.state == 'assigned')
        self.assertEqual(len(picking_ret), 1)
        picking_ret.action_confirm()
        picking_ret.action_assign()
        for move in picking_ret.move_lines:
            move.quantity_done = move.product_uom_qty
        picking_ret.action_done()
        ctx = {
            'tracking_disable': True,
            'mail_notrack': True,
            'mail_create_nolog': True,
            'active_model': 'sale.order',
            'active_ids': sale.ids,
            'active_id': sale.id,
        }
        wizard = self.env['sale.advance.payment.inv'].with_context(ctx).create(
            {'advance_payment_method': 'all'})
        wizard.create_invoices()
        self.assertEqual(len(sale.invoice_ids), 2)
        refund = sale.invoice_ids.filtered(lambda i: i.type == 'out_refund')
        self.assertEqual(len(refund), 1)
        self.assertNotEqual(
            refund.invoice_line_ids.account_id,
            product.property_account_sales_refund_id)
        self.assertNotEqual(
            refund.invoice_line_ids.account_id,
            product.categ_id.property_account_sales_refund_id)
        self.assertNotEqual(
            refund.invoice_line_ids.account_id, self.account_sale_test)
        self.assertEqual(refund.invoice_line_ids.account_id, default_account)

    def test_sale_advance_invoice_wizard_02(self):
        product = self.env['product.product'].create({
            'type': 'product',
            'company_id': False,
            'name': 'Product test 3',
            'standard_price': 10,
            'list_price': 100,
        })
        product.invoice_policy = 'delivery'
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': product.id,
                    'price_unit': 100,
                    'product_uom_qty': 1,
                }),
            ],
        })
        sale.action_confirm()
        self.assertEqual(len(sale.picking_ids), 1)
        picking = sale.picking_ids[0]
        picking.action_confirm()
        picking.action_assign()
        for move in picking.move_lines:
            move.quantity_done = move.product_uom_qty
        picking.action_done()
        self.assertEqual(picking.state, 'done')
        ctx = {
            'tracking_disable': True,
            'mail_notrack': True,
            'mail_create_nolog': True,
            'active_model': 'sale.order',
            'active_ids': sale.ids,
            'active_id': sale.id,
        }
        wizard = self.env['sale.advance.payment.inv'].with_context(ctx).create(
            {'advance_payment_method': 'all'})
        wizard.create_invoices()
        self.assertEqual(len(sale.invoice_ids), 1)
        return_picking = self.env['stock.return.picking'].with_context(
            active_ids=picking.ids,
            active_id=picking.id,
        ).create({})
        return_picking.product_return_moves.write({
            'quantity': 1,
            'to_refund': True,
        })
        return_picking.create_returns()
        self.assertEqual(len(sale.picking_ids), 2)
        picking_ret = sale.picking_ids.filtered(
            lambda p: p.state == 'assigned')
        self.assertEqual(len(picking_ret), 1)
        picking_ret.action_confirm()
        picking_ret.action_assign()
        for move in picking_ret.move_lines:
            move.quantity_done = move.product_uom_qty
        picking_ret.action_done()
        self.assertFalse(product.property_account_sales_refund_id)
        self.assertFalse(product.categ_id.property_account_sales_refund_id)
        product.property_account_sales_refund_id = self.account_sale_test.id
        self.assertEqual(
            product.property_account_sales_refund_id, self.account_sale_test)
        ctx = {
            'tracking_disable': True,
            'mail_notrack': True,
            'mail_create_nolog': True,
            'active_model': 'sale.order',
            'active_ids': sale.ids,
            'active_id': sale.id,
        }
        wizard = self.env['sale.advance.payment.inv'].with_context(ctx).create(
            {'advance_payment_method': 'all'})
        wizard.create_invoices()
        self.assertEqual(len(sale.invoice_ids), 2)
        refund = sale.invoice_ids.filtered(lambda i: i.type == 'out_refund')
        self.assertEqual(len(refund), 1)
        self.assertEqual(
            refund.invoice_line_ids.account_id,
            product.property_account_sales_refund_id)
        self.assertNotEqual(
            refund.invoice_line_ids.account_id,
            product.categ_id.property_account_sales_refund_id)
        self.assertEqual(
            refund.invoice_line_ids.account_id, self.account_sale_test)

    def test_sale_advance_invoice_wizard_03(self):
        product = self.env['product.product'].create({
            'type': 'product',
            'company_id': False,
            'name': 'Product test 3',
            'standard_price': 10,
            'list_price': 100,
        })
        product.invoice_policy = 'delivery'
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': product.id,
                    'price_unit': 100,
                    'product_uom_qty': 1,
                }),
            ],
        })
        sale.action_confirm()
        self.assertEqual(len(sale.picking_ids), 1)
        picking = sale.picking_ids[0]
        picking.action_confirm()
        picking.action_assign()
        for move in picking.move_lines:
            move.quantity_done = move.product_uom_qty
        picking.action_done()
        self.assertEqual(picking.state, 'done')
        ctx = {
            'tracking_disable': True,
            'mail_notrack': True,
            'mail_create_nolog': True,
            'active_model': 'sale.order',
            'active_ids': sale.ids,
            'active_id': sale.id,
        }
        wizard = self.env['sale.advance.payment.inv'].with_context(ctx).create(
            {'advance_payment_method': 'all'})
        wizard.create_invoices()
        self.assertEqual(len(sale.invoice_ids), 1)
        return_picking = self.env['stock.return.picking'].with_context(
            active_ids=picking.ids,
            active_id=picking.id,
        ).create({})
        return_picking.product_return_moves.write({
            'quantity': 1,
            'to_refund': True,
        })
        return_picking.create_returns()
        self.assertEqual(len(sale.picking_ids), 2)
        picking_ret = sale.picking_ids.filtered(
            lambda p: p.state == 'assigned')
        self.assertEqual(len(picking_ret), 1)
        picking_ret.action_confirm()
        picking_ret.action_assign()
        for move in picking_ret.move_lines:
            move.quantity_done = move.product_uom_qty
        picking_ret.action_done()
        self.assertFalse(product.property_account_sales_refund_id)
        self.assertFalse(product.categ_id.property_account_sales_refund_id)
        product.categ_id.property_account_sales_refund_id = (
            self.account_sale_test.id)
        self.assertEqual(
            product.categ_id.property_account_sales_refund_id,
            self.account_sale_test)
        ctx = {
            'tracking_disable': True,
            'mail_notrack': True,
            'mail_create_nolog': True,
            'active_model': 'sale.order',
            'active_ids': sale.ids,
            'active_id': sale.id,
        }
        wizard = self.env['sale.advance.payment.inv'].with_context(ctx).create(
            {'advance_payment_method': 'all'})
        wizard.create_invoices()
        self.assertEqual(len(sale.invoice_ids), 2)
        refund = sale.invoice_ids.filtered(lambda i: i.type == 'out_refund')
        self.assertEqual(len(refund), 1)
        self.assertNotEqual(
            refund.invoice_line_ids.account_id,
            product.property_account_sales_refund_id)
        self.assertEqual(
            refund.invoice_line_ids.account_id,
            product.categ_id.property_account_sales_refund_id)
        self.assertEqual(
            refund.invoice_line_ids.account_id, self.account_sale_test)

    def test_sale_advance_invoice_wizard_04(self):
        product = self.env['product.product'].create({
            'type': 'product',
            'company_id': False,
            'name': 'Product test 3',
            'standard_price': 10,
            'list_price': 100,
        })
        product.invoice_policy = 'delivery'
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': product.id,
                    'price_unit': 100,
                    'product_uom_qty': 1,
                }),
            ],
        })
        sale.action_confirm()
        self.assertEqual(len(sale.picking_ids), 1)
        picking = sale.picking_ids[0]
        picking.action_confirm()
        picking.action_assign()
        for move in picking.move_lines:
            move.quantity_done = move.product_uom_qty
        picking.action_done()
        self.assertEqual(picking.state, 'done')
        ctx = {
            'tracking_disable': True,
            'mail_notrack': True,
            'mail_create_nolog': True,
            'active_model': 'sale.order',
            'active_ids': sale.ids,
            'active_id': sale.id,
        }
        wizard = self.env['sale.advance.payment.inv'].with_context(ctx).create(
            {'advance_payment_method': 'all'})
        wizard.create_invoices()
        self.assertEqual(len(sale.invoice_ids), 1)
        return_picking = self.env['stock.return.picking'].with_context(
            active_ids=picking.ids,
            active_id=picking.id,
        ).create({})
        return_picking.product_return_moves.write({
            'quantity': 1,
            'to_refund': True,
        })
        return_picking.create_returns()
        self.assertEqual(len(sale.picking_ids), 2)
        picking_ret = sale.picking_ids.filtered(
            lambda p: p.state == 'assigned')
        self.assertEqual(len(picking_ret), 1)
        picking_ret.action_confirm()
        picking_ret.action_assign()
        for move in picking_ret.move_lines:
            move.quantity_done = move.product_uom_qty
        picking_ret.action_done()
        self.assertFalse(product.property_account_sales_refund_id)
        self.assertFalse(product.categ_id.property_account_sales_refund_id)
        product.property_account_sales_refund_id = (
            self.account_sale_test)
        product.categ_id.property_account_sales_refund_id = (
            self.account_customer_test)
        self.assertEqual(
            product.property_account_sales_refund_id,
            self.account_sale_test)
        self.assertEqual(
            product.categ_id.property_account_sales_refund_id,
            self.account_customer_test)
        self.assertNotEqual(
            product.property_account_sales_refund_id,
            product.categ_id.property_account_sales_refund_id)
        ctx = {
            'tracking_disable': True,
            'mail_notrack': True,
            'mail_create_nolog': True,
            'active_model': 'sale.order',
            'active_ids': sale.ids,
            'active_id': sale.id,
        }
        wizard = self.env['sale.advance.payment.inv'].with_context(ctx).create(
            {'advance_payment_method': 'all'})
        wizard.create_invoices()
        self.assertEqual(len(sale.invoice_ids), 2)
        refund = sale.invoice_ids.filtered(lambda i: i.type == 'out_refund')
        self.assertEqual(len(refund), 1)
        self.assertEqual(
            refund.invoice_line_ids.account_id,
            product.property_account_sales_refund_id)
        self.assertNotEqual(
            refund.invoice_line_ids.account_id,
            product.categ_id.property_account_sales_refund_id)
        self.assertEqual(
            refund.invoice_line_ids.account_id, self.account_sale_test)

    def test_multiple_invoices_from_sales(self):
        product_01 = self.env['product.product'].create({
            'type': 'product',
            'company_id': False,
            'name': 'Product test 4',
            'standard_price': 10,
            'list_price': 100,
        })
        product_01.invoice_policy = 'delivery'
        sale_01 = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': product_01.id,
                    'price_unit': 50,
                    'product_uom_qty': 1,
                }),
            ],
        })
        partner_02 = self.env['res.partner'].create({
            'name': 'Partner test 2',
        })
        product_02 = self.env['product.product'].create({
            'type': 'product',
            'company_id': False,
            'name': 'Product test 5',
            'standard_price': 10,
            'list_price': 100,
        })
        product_02.invoice_policy = 'delivery'
        sale_02 = self.env['sale.order'].create({
            'partner_id': partner_02.id,
            'order_line': [
                (0, 0, {
                    'product_id': product_02.id,
                    'price_unit': 30,
                    'product_uom_qty': 1,
                }),
            ],
        })
        sale_01.action_confirm()
        sale_02.action_confirm()
        self.assertEqual(len(sale_01.picking_ids), 1)
        self.assertEqual(len(sale_02.picking_ids), 1)
        picking_01 = sale_01.picking_ids[0]
        picking_01.action_confirm()
        picking_01.action_assign()
        for move in picking_01.move_lines:
            move.quantity_done = move.product_uom_qty
        picking_01.action_done()
        picking_02 = sale_02.picking_ids[0]
        picking_02.action_confirm()
        picking_02.action_assign()
        for move in picking_02.move_lines:
            move.quantity_done = move.product_uom_qty
        picking_02.action_done()
        self.assertEqual(picking_01.state, 'done')
        self.assertEqual(picking_02.state, 'done')
        ctx = {
            'tracking_disable': True,
            'mail_notrack': True,
            'mail_create_nolog': True,
            'active_model': 'sale.order',
            'active_ids': sale_01.ids,
            'active_id': sale_01.id,
        }
        wizard_01 = self.env['sale.advance.payment.inv'].with_context(
            ctx).create({'advance_payment_method': 'all'})
        wizard_01.create_invoices()
        ctx = {
            'tracking_disable': True,
            'mail_notrack': True,
            'mail_create_nolog': True,
            'active_model': 'sale.order',
            'active_ids': sale_02.ids,
            'active_id': sale_02.id,
        }
        wizard_02 = self.env['sale.advance.payment.inv'].with_context(
            ctx).create({'advance_payment_method': 'all'})
        wizard_02.create_invoices()
        self.assertEqual(len(sale_01.invoice_ids), 1)
        self.assertEqual(len(sale_02.invoice_ids), 1)
        return_picking_01 = self.env['stock.return.picking'].with_context(
            active_ids=picking_01.ids,
            active_id=picking_01.id,
        ).create({})
        return_picking_01.product_return_moves.write({
            'quantity': 1,
            'to_refund': True,
        })
        return_picking_01.create_returns()
        return_picking_02 = self.env['stock.return.picking'].with_context(
            active_ids=picking_02.ids,
            active_id=picking_02.id,
        ).create({})
        return_picking_02.product_return_moves.write({
            'quantity': 1,
            'to_refund': True,
        })
        return_picking_02.create_returns()
        self.assertEqual(len(sale_01.picking_ids), 2)
        self.assertEqual(len(sale_02.picking_ids), 2)
        picking_ret_01 = sale_01.picking_ids.filtered(
            lambda p: p.state == 'assigned')
        self.assertEqual(len(picking_ret_01), 1)
        picking_ret_01.action_confirm()
        picking_ret_01.action_assign()
        for move in picking_ret_01.move_lines:
            move.quantity_done = move.product_uom_qty
        picking_ret_01.action_done()
        picking_ret_02 = sale_02.picking_ids.filtered(
            lambda p: p.state == 'assigned')
        self.assertEqual(len(picking_ret_02), 1)
        picking_ret_02.action_confirm()
        picking_ret_02.action_assign()
        for move in picking_ret_02.move_lines:
            move.quantity_done = move.product_uom_qty
        picking_ret_02.action_done()
        self.assertFalse(product_01.property_account_sales_refund_id)
        self.assertFalse(product_02.property_account_sales_refund_id)
        self.assertFalse(product_01.categ_id.property_account_sales_refund_id)
        self.assertFalse(product_02.categ_id.property_account_sales_refund_id)
        product_01.property_account_sales_refund_id = (
            self.account_sale_test)
        product_01.categ_id.property_account_sales_refund_id = (
            self.account_customer_test)
        product_02.property_account_sales_refund_id = (
            self.account_sale_test)
        product_02.categ_id.property_account_sales_refund_id = (
            self.account_customer_test)
        self.assertEqual(
            product_01.property_account_sales_refund_id,
            self.account_sale_test)
        self.assertEqual(
            product_01.categ_id.property_account_sales_refund_id,
            self.account_customer_test)
        self.assertNotEqual(
            product_01.property_account_sales_refund_id,
            product_01.categ_id.property_account_sales_refund_id)
        self.assertEqual(
            product_02.property_account_sales_refund_id,
            self.account_sale_test)
        self.assertEqual(
            product_02.categ_id.property_account_sales_refund_id,
            self.account_customer_test)
        self.assertNotEqual(
            product_02.property_account_sales_refund_id,
            product_02.categ_id.property_account_sales_refund_id)
        ctx = {
            'tracking_disable': True,
            'mail_notrack': True,
            'mail_create_nolog': True,
            'active_model': 'sale.order',
            'active_ids': [sale_01.id, sale_02.id],
            'active_id': sale_01.id,
        }
        wizard = self.env['sale.advance.payment.inv'].with_context(ctx).create(
            {'advance_payment_method': 'all'})
        wizard.create_invoices()
        self.assertEqual(len(sale_01.invoice_ids), 2)
        self.assertEqual(len(sale_02.invoice_ids), 2)
        refund_01 = sale_01.invoice_ids.filtered(
            lambda i: i.type == 'out_refund')
        refund_02 = sale_02.invoice_ids.filtered(
            lambda i: i.type == 'out_refund')
        self.assertEqual(len(refund_01), 1)
        self.assertEqual(len(refund_02), 1)
        self.assertEqual(
            refund_01.invoice_line_ids.account_id,
            product_01.property_account_sales_refund_id)
        self.assertNotEqual(
            refund_01.invoice_line_ids.account_id,
            product_01.categ_id.property_account_sales_refund_id)
        self.assertEqual(
            refund_01.invoice_line_ids.account_id, self.account_sale_test)
        self.assertEqual(
            refund_02.invoice_line_ids.account_id,
            product_02.property_account_sales_refund_id)
        self.assertNotEqual(
            refund_02.invoice_line_ids.account_id,
            product_02.categ_id.property_account_sales_refund_id)
        self.assertEqual(
            refund_02.invoice_line_ids.account_id, self.account_sale_test)

    def test_purchase_order_invoice(self):
        product = self.env['product.product'].create({
            'type': 'product',
            'company_id': False,
            'name': 'Product test',
            'standard_price': 10,
            'list_price': 60,
        })
        self.assertTrue(product.categ_id.property_stock_account_input_categ_id)
        default_account = (
            product.categ_id.property_stock_account_input_categ_id)
        product.property_account_purchase_refund_id = (
            self.account_customer_test.id)
        purchase = self.env['purchase.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'name': product.name,
                    'product_id': product.id,
                    'product_uom': product.uom_po_id.id,
                    'price_unit': product.standard_price,
                    'product_qty': 1,
                    'date_planned': fields.Date.today(),
                }),
            ],
        })
        purchase.button_confirm()
        self.assertEqual(purchase.invoice_status, 'no')
        self.assertEqual(len(purchase.picking_ids), 1)
        picking = purchase.picking_ids[0]
        picking.action_confirm()
        picking.action_assign()
        for move in picking.move_lines:
            move.quantity_done = move.product_uom_qty
        picking.action_done()
        self.assertEqual(purchase.invoice_status, 'to invoice')
        wizard_01 = self.env['purchase.order.invoice'].with_context({
            'active_id': purchase.id,
            'active_ids': purchase.ids,
            'active_model': 'purchase.order',
        }).create({
            'method': 'received',
        })
        self.assertEqual(len(purchase.invoice_ids), 0)
        wizard_01.action_invoice()
        self.assertEqual(len(purchase.invoice_ids), 1)
        purchase.invoice_ids[0].action_invoice_open()
        self.assertEqual(purchase.invoice_status, 'invoiced')
        return_picking = self.env['stock.return.picking'].with_context(
            active_ids=picking.ids,
            active_id=picking.id,
        ).create({})
        return_picking.product_return_moves.write({
            'quantity': 1,
            'to_refund': True,
        })
        return_picking.create_returns()
        self.assertEqual(len(purchase.picking_ids), 2)
        picking_ret = purchase.picking_ids.filtered(
            lambda p: p.state == 'assigned')
        self.assertEqual(len(picking_ret), 1)
        picking_ret.action_confirm()
        picking_ret.action_assign()
        for move in picking_ret.move_lines:
            move.quantity_done = move.product_uom_qty
        picking_ret.action_done()
        wizard_02 = self.env['purchase.order.invoice'].with_context({
            'active_id': purchase.id,
            'active_ids': purchase.ids,
            'active_model': 'purchase.order',
        }).create({
            'method': 'received',
        })
        wizard_02.action_invoice()
        self.assertEqual(len(purchase.invoice_ids), 2)
        invoice_refund = purchase.invoice_ids.filtered(
            lambda i: i.type == 'in_refund')
        self.assertEqual(len(invoice_refund), 1)
        refund_line_01 = invoice_refund.invoice_line_ids[0]
        self.assertNotEqual(refund_line_01.account_id, default_account)
        self.assertEqual(refund_line_01.account_id, self.account_customer_test)
        self.assertEqual(
            refund_line_01.account_id,
            product.property_account_purchase_refund_id)
