###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields
from odoo.exceptions import ValidationError
from odoo.tests import common


class TestSaleOrderLineSupplierinfo(common.TransactionCase):

    def setUp(self):
        super().setUp()
        route = self.env.ref('stock.route_warehouse0_mto')
        self.product_a = self.env['product.product'].create({
            'type': 'product',
            'name': 'Product test A',
            'standard_price': 10,
            'list_price': 100,
        })
        self.product_b = self.env['product.product'].create({
            'type': 'product',
            'name': 'Product test B',
            'standard_price': 10,
            'list_price': 100,
            'route_ids': [(6, 0, route.ids)],
        })
        self.partner = self.env['res.partner'].create({
            'name': 'Test partner',
            'is_company': True,
        })
        self.supplier = self.env['res.partner'].create({
            'name': 'Test supplier',
            'is_company': True,
        })
        route = self.env['stock.route'].create({
            'name': 'Test route ',
            'product_selectable': True,
            'rule_ids': [(0, 0, {
                'sequence': -1000,
                'name': 'Test rule',
                'action': 'pull',
                'picking_type_id': self.ref('stock.picking_type_out'),
                'location_src_id': self.ref('stock.stock_location_stock'),
                'location_dest_id': self.ref('stock.stock_location_customers'),
            })],
        })
        self.supplierinfo_a1 = self.env['product.supplierinfo'].create({
            'partner_id': self.supplier.id,
            'product_tmpl_id': self.product_a.product_tmpl_id.id,
            'product_code': 'A1',
            'route_select': 'product',
            'sequence': 10,
        })
        self.supplierinfo_a2 = self.env['product.supplierinfo'].create({
            'partner_id': self.supplier.id,
            'product_tmpl_id': self.product_a.product_tmpl_id.id,
            'product_code': 'A2',
            'route_select': 'customize',
            'route_ids': [(6, 0, route.ids)],
            'sequence': 20,
        })
        self.supplierinfo_b1 = self.env['product.supplierinfo'].create({
            'partner_id': self.supplier.id,
            'product_tmpl_id': self.product_b.product_tmpl_id.id,
            'product_code': 'B1',
            'route_select': 'customize',
            'sequence': 0,
        })

    def test_supplierinfo_default(self):
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'pricelist_id': self.env.ref('product.list0').id,
        })
        line_obj = self.env['sale.order.line']
        line = line_obj.new({
            'order_id': sale.id,
            'product_id': self.product_a.id,
            'product_uom_qty': 10,
            'product_uom': self.product_a.uom_id.id,
        })
        line.product_id_change()
        line = line_obj.create(line_obj._convert_to_write(line._cache))
        self.assertTrue(line.supplierinfo_id)
        self.assertEqual(line.supplierinfo_id, self.supplierinfo_a1)
        sale.action_confirm()
        sale_2 = sale.copy()
        sale_2.order_line.supplierinfo_id = False
        sale_2.action_confirm()
        self.assertEqual(
            sale.order_line.move_ids.rule_id.route_id,
            sale_2.order_line.move_ids.rule_id.route_id)
        sale = sale.copy()
        line = sale.order_line[0]
        line.supplierinfo_id = self.supplierinfo_a2
        sale.action_confirm()
        self.assertEqual(
            self.supplierinfo_a2.route_ids[0], line.move_ids.rule_id.route_id)

    def test_change_supplierinfo(self):
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'pricelist_id': self.env.ref('product.list0').id,
        })
        line_obj = self.env['sale.order.line']
        line = line_obj.new({
            'order_id': sale.id,
            'product_id': self.product_a.id,
            'product_uom_qty': 10,
            'product_uom': self.product_a.uom_id.id,
        })
        line.product_id_change()
        line = line_obj.create(line_obj._convert_to_write(line._cache))
        self.assertTrue(line.supplierinfo_id)
        self.assertEqual(line.vendor_id, line.supplierinfo_id.partner_id)
        self.assertEqual(line.supplierinfo_id, self.supplierinfo_a1)
        with self.assertRaises(ValidationError):
            line.supplierinfo_id = self.supplierinfo_b1.id
        line.supplierinfo_id = self.supplierinfo_a2.id
        self.assertEqual(line.supplierinfo_id, self.supplierinfo_a2)
        self.assertEqual(line.vendor_id, self.supplierinfo_a2.partner_id)
        sale.action_confirm()
        self.assertEqual(
            self.supplierinfo_a2.route_ids[0], line.move_ids.rule_id.route_id)

    def test_make_po_select_supplier_route_buy_forced_by_sale_order_line(self):
        module = self.env['ir.module.module'].sudo().search([
            ('name', '=', 'purchase'),
            ('state', '=', 'installed'),
        ])
        if not module:
            self.skipTest('No module purchase installed')
        mto_route = self.env.ref('stock.route_warehouse0_mto')
        buy_route = self.env.ref('purchase_stock.route_warehouse0_buy')
        product_1 = self.env['product.product'].create({
            'type': 'product',
            'name': 'Product test 1',
            'standard_price': 10,
            'list_price': 100,
            'route_ids': [(6, 0, buy_route.ids)],
        })
        self.supplierinfo_p1_1 = self.env['product.supplierinfo'].create({
            'partner_id': self.supplier.id,
            'product_tmpl_id': product_1.product_tmpl_id.id,
            'product_code': 'P1',
            'route_select': 'product',
            'sequence': 10,
        })
        supplier_2 = self.env['res.partner'].create({
            'name': 'Test supplier 2',
            'is_company': True,
        })
        self.supplierinfo_p1_2 = self.env['product.supplierinfo'].create({
            'partner_id': supplier_2.id,
            'product_tmpl_id': product_1.product_tmpl_id.id,
            'product_code': 'P1',
            'route_select': 'product',
            'sequence': 20,
        })
        self.assertIn(self.supplierinfo_p1_1, product_1.seller_ids)
        self.assertIn(self.supplierinfo_p1_2, product_1.seller_ids)
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'pricelist_id': self.env.ref('product.list0').id,
        })
        line_obj = self.env['sale.order.line']
        line = line_obj.new({
            'order_id': sale.id,
            'product_id': product_1.id,
            'product_uom_qty': 10,
            'product_uom': product_1.uom_id.id,
        })
        line.product_id_change()
        line = line_obj.create(line_obj._convert_to_write(line._cache))
        self.assertTrue(line.supplierinfo_id)
        self.assertEqual(line.supplierinfo_id, self.supplierinfo_p1_1)
        line.supplierinfo_id = self.supplierinfo_p1_2.id
        self.assertEqual(line.supplierinfo_id, self.supplierinfo_p1_2)
        line.route_id = mto_route.id
        sale.action_confirm()
        purchase = self.env['purchase.order'].search([
            ('origin', '=', sale.name),
        ])
        self.assertEqual(len(purchase), 1)
        self.assertEqual(
            purchase.partner_id, self.supplierinfo_p1_2.partner_id)
        self.assertEqual(purchase.partner_id, supplier_2)

    def test_make_po_get_domain_keeps_group_for_dropship(self):
        buy_rule = self.env.ref('stock.warehouse0').buy_pull_id
        buy_rule.group_propagation_option = 'propagate'
        group = self.env['procurement.group'].create({'name': 'Test group'})
        standard_product = self.env['product.product'].create({
            'type': 'product',
            'name': 'Standard product',
            'standard_price': 10,
            'list_price': 100,
        })
        standard_sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'pricelist_id': self.env.ref('product.list0').id,
        })
        standard_line = self.env['sale.order.line'].create({
            'order_id': standard_sale.id,
            'product_id': standard_product.id,
            'product_uom_qty': 1,
            'product_uom': standard_product.uom_id.id,
        })
        standard_values = standard_line._prepare_procurement_values(group)
        standard_domain = buy_rule._make_po_get_domain(
            self.env.company, standard_values, self.supplier)
        self.assertNotIn(('group_id', '=', group.id), standard_domain)
        dropship_route = self.env.ref('stock_dropshipping.route_drop_shipping')
        dropship_product = self.env['product.product'].create({
            'type': 'product',
            'name': 'Dropship product',
            'standard_price': 10,
            'list_price': 100,
            'route_ids': [(6, 0, dropship_route.ids)],
        })
        dropship_sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'pricelist_id': self.env.ref('product.list0').id,
        })
        dropship_line = self.env['sale.order.line'].create({
            'order_id': dropship_sale.id,
            'product_id': dropship_product.id,
            'product_uom_qty': 1,
            'product_uom': dropship_product.uom_id.id,
        })
        dropship_values = dropship_line._prepare_procurement_values(group)
        dropship_domain = buy_rule._make_po_get_domain(
            self.env.company, dropship_values, self.supplier)
        self.assertIn(('group_id', '=', group.id), dropship_domain)

    def test_dropship_sales_do_not_group_into_same_purchase_order(self):
        dropship_route = self.env.ref('stock_dropshipping.route_drop_shipping')
        product = self.env['product.product'].create({
            'type': 'product',
            'name': 'Dropship grouped product',
            'standard_price': 10,
            'list_price': 100,
            'route_ids': [(6, 0, dropship_route.ids)],
        })
        self.env['product.supplierinfo'].create({
            'partner_id': self.supplier.id,
            'product_tmpl_id': product.product_tmpl_id.id,
            'sequence': 10,
        })
        sale_1 = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'pricelist_id': self.env.ref('product.list0').id,
        })
        line_1 = self.env['sale.order.line'].create({
            'order_id': sale_1.id,
            'product_id': product.id,
            'product_uom_qty': 1,
            'product_uom': product.uom_id.id,
        })
        line_1.product_id_change()
        self.assertTrue(line_1.supplierinfo_id)
        sale_1.action_confirm()
        customer_2 = self.env['res.partner'].create({
            'name': 'Second customer',
            'is_company': True,
        })
        sale_2 = self.env['sale.order'].create({
            'partner_id': customer_2.id,
            'pricelist_id': self.env.ref('product.list0').id,
        })
        line_2 = self.env['sale.order.line'].create({
            'order_id': sale_2.id,
            'product_id': product.id,
            'product_uom_qty': 1,
            'product_uom': product.uom_id.id,
        })
        line_2.product_id_change()
        self.assertTrue(line_2.supplierinfo_id)
        sale_2.action_confirm()
        purchases = self.env['purchase.order'].search([
            ('origin', 'in', [sale_1.name, sale_2.name]),
        ])
        self.assertEqual(len(purchases), 2)
        self.assertEqual(
            set(purchases.mapped('origin')), {sale_1.name, sale_2.name})
        purchase_1 = purchases.filtered(lambda po: po.origin == sale_1.name)
        purchase_2 = purchases.filtered(lambda po: po.origin == sale_2.name)
        self.assertEqual(len(purchase_1.order_line), 1)
        self.assertEqual(len(purchase_2.order_line), 1)

    def test_run_buy_select_supplier_from_orderpoint_sale_origin(self):
        warehouse = self.env.ref('stock.warehouse0')
        buy_rule = warehouse.buy_pull_id
        product = self.env['product.product'].create({
            'type': 'product',
            'name': 'Product test orderpoint',
            'standard_price': 10,
            'list_price': 100,
        })
        supplier_1 = self.env['res.partner'].create({
            'name': 'Test supplier 1',
            'is_company': True,
        })
        supplier_2 = self.env['res.partner'].create({
            'name': 'Test supplier 2',
            'is_company': True,
        })
        supplierinfo_1 = self.env['product.supplierinfo'].create({
            'partner_id': supplier_1.id,
            'product_tmpl_id': product.product_tmpl_id.id,
            'sequence': 10,
        })
        supplierinfo_2 = self.env['product.supplierinfo'].create({
            'partner_id': supplier_2.id,
            'product_tmpl_id': product.product_tmpl_id.id,
            'sequence': 20,
        })
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'pricelist_id': self.env.ref('product.list0').id,
            'warehouse_id': warehouse.id,
        })
        line = self.env['sale.order.line'].create({
            'order_id': sale.id,
            'product_id': product.id,
            'product_uom_qty': 2,
            'product_uom': product.uom_id.id,
            'supplierinfo_id': supplierinfo_2.id,
        })
        self.assertEqual(line.vendor_id, supplier_2)
        sale.action_confirm()
        orderpoint = self.env['stock.warehouse.orderpoint'].create({
            'name': 'OP test supplierinfo',
            'warehouse_id': warehouse.id,
            'location_id': warehouse.lot_stock_id.id,
            'product_id': product.id,
            'product_min_qty': 0,
            'product_max_qty': 2,
            'qty_to_order': 2,
            'trigger': 'manual',
            'supplier_id': supplierinfo_1.id,
            'route_id': buy_rule.route_id.id,
        })
        procurement = self.env['procurement.group'].Procurement(
            product, 2, product.uom_id, warehouse.lot_stock_id, buy_rule.name,
            '%s - %s' % (orderpoint.display_name, sale.name),
            sale.company_id, {
                'warehouse_id': warehouse,
                'date_planned': fields.Datetime.now(),
                'group_id': False,
                'orderpoint_id': orderpoint,
                'route_ids': [],
                'rule_id': buy_rule,
            }
        )
        buy_rule._run_buy([(procurement, buy_rule)])
        purchase = self.env['purchase.order'].search([
            ('origin', '=', '%s - %s' % (orderpoint.display_name, sale.name)),
        ])
        self.assertEqual(len(purchase), 1)
        self.assertEqual(purchase.partner_id, supplier_2)

    def test_make_po_select_supplier_route_dropship_forced_by_sale_order_line(
            self):
        dropshipping_route = self.env.ref(
            'stock_dropshipping.route_drop_shipping')
        product_1 = self.env['product.product'].create({
            'type': 'product',
            'name': 'Product test 1',
            'standard_price': 10,
            'list_price': 100,
            'route_ids': [(6, 0, dropshipping_route.ids)],
        })
        self.supplierinfo_p1_1 = self.env['product.supplierinfo'].create({
            'partner_id': self.supplier.id,
            'product_tmpl_id': product_1.product_tmpl_id.id,
            'product_code': 'P1',
            'route_select': 'product',
            'sequence': 10,
        })
        supplier_2 = self.env['res.partner'].create({
            'name': 'Test supplier 2',
            'is_company': True,
        })
        self.supplierinfo_p1_2 = self.env['product.supplierinfo'].create({
            'partner_id': supplier_2.id,
            'product_tmpl_id': product_1.product_tmpl_id.id,
            'product_code': 'P1',
            'route_select': 'product',
            'sequence': 20,
        })
        self.assertIn(self.supplierinfo_p1_1, product_1.seller_ids)
        self.assertIn(self.supplierinfo_p1_2, product_1.seller_ids)
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'pricelist_id': self.env.ref('product.list0').id,
        })
        line_obj = self.env['sale.order.line']
        line = line_obj.new({
            'order_id': sale.id,
            'product_id': product_1.id,
            'product_uom_qty': 10,
            'product_uom': product_1.uom_id.id,
        })
        line.product_id_change()
        line = line_obj.create(line_obj._convert_to_write(line._cache))
        self.assertTrue(line.supplierinfo_id)
        self.assertEqual(line.supplierinfo_id, self.supplierinfo_p1_1)
        line.supplierinfo_id = self.supplierinfo_p1_2.id
        self.assertEqual(line.supplierinfo_id, self.supplierinfo_p1_2)
        line.route_id = dropshipping_route.id
        sale.action_confirm()
        purchase = self.env['purchase.order'].search([
            ('origin', '=', sale.name),
        ])
        self.assertEqual(len(purchase), 1)
        self.assertEqual(
            purchase.partner_id, self.supplierinfo_p1_2.partner_id)
        self.assertEqual(purchase.partner_id, supplier_2)

    def test_reuse_draft_purchase_order_for_supplier(self):
        module = self.env['ir.module.module'].sudo().search([
            ('name', '=', 'purchase'),
            ('state', '=', 'installed'),
        ])
        if not module:
            self.skipTest('No module purchase installed')
        mto_route = self.env.ref('stock.route_warehouse0_mto')
        buy_route = self.env.ref('purchase_stock.route_warehouse0_buy')
        product = self.env['product.product'].create({
            'type': 'product',
            'name': 'Product test reuse draft po',
            'standard_price': 10,
            'list_price': 100,
            'route_ids': [(6, 0, buy_route.ids)],
        })
        supplier_2 = self.env['res.partner'].create({
            'name': 'Test supplier 2',
            'is_company': True,
        })
        supplierinfo_2 = self.env['product.supplierinfo'].create({
            'partner_id': supplier_2.id,
            'product_tmpl_id': product.product_tmpl_id.id,
            'product_code': 'P2',
            'route_select': 'product',
            'sequence': 20,
        })
        purchase = self.env['purchase.order'].create({
            'partner_id': supplier_2.id,
            'picking_type_id': self.env.ref('stock.picking_type_in').id,
            'user_id': False,
        })
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'pricelist_id': self.env.ref('product.list0').id,
        })
        line_obj = self.env['sale.order.line']
        line = line_obj.new({
            'order_id': sale.id,
            'product_id': product.id,
            'product_uom_qty': 5,
            'product_uom': product.uom_id.id,
        })
        line.product_id_change()
        line = line_obj.create(line_obj._convert_to_write(line._cache))
        line.supplierinfo_id = supplierinfo_2.id
        line.route_id = mto_route.id
        sale.action_confirm()
        copy_sale = sale.copy()
        copy_sale.action_confirm()
        purchases = self.env['purchase.order'].search([
            ('partner_id', '=', supplier_2.id),
            ('state', '=', 'draft'),
        ])
        self.assertEqual(len(purchases), 1)
        self.assertEqual(purchases, purchase)
        self.assertEqual(len(purchase.order_line), 1)
        self.assertEqual(purchase.order_line.product_id, product)
