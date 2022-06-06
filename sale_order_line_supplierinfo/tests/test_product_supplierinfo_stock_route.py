###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
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
        route = self.env['stock.location.route'].create({
            'name': 'Test route ',
            'product_selectable': True,
            'rule_ids': [(0, 0, {
                'sequence': -1000,
                'name': 'Test rule',
                'action': 'pull',
                'picking_type_id': self.ref('stock.picking_type_out'),
                'location_src_id': self.ref('stock.stock_location_stock'),
                'location_id': self.ref('stock.stock_location_customers'),
            })],
        })
        self.supplierinfo_a1 = self.env['product.supplierinfo'].create({
            'name': self.supplier.id,
            'product_tmpl_id': self.product_a.product_tmpl_id.id,
            'product_code': 'A1',
            'route_select': 'product',
            'sequence': 10,
        })
        self.supplierinfo_a2 = self.env['product.supplierinfo'].create({
            'name': self.supplier.id,
            'product_tmpl_id': self.product_a.product_tmpl_id.id,
            'product_code': 'A2',
            'route_select': 'customize',
            'route_ids': [(6, 0, route.ids)],
            'sequence': 20,
        })
        self.supplierinfo_b1 = self.env['product.supplierinfo'].create({
            'name': self.supplier.id,
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
        self.assertEquals(line.supplierinfo_id, self.supplierinfo_a1)
        sale.action_confirm()
        sale_2 = sale.copy()
        sale_2.order_line.supplierinfo_id = False
        sale_2.action_confirm()
        self.assertEquals(
            sale.order_line.move_ids.rule_id.route_id,
            sale_2.order_line.move_ids.rule_id.route_id)
        sale = sale.copy()
        line = sale.order_line[0]
        line.supplierinfo_id = self.supplierinfo_a2
        sale.action_confirm()
        self.assertEquals(
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
        self.assertEquals(line.vendor_id, line.supplierinfo_id.name)
        self.assertEquals(line.supplierinfo_id, self.supplierinfo_a1)
        with self.assertRaises(ValidationError):
            line.supplierinfo_id = self.supplierinfo_b1.id
        line.supplierinfo_id = self.supplierinfo_a2.id
        self.assertEquals(line.supplierinfo_id, self.supplierinfo_a2)
        self.assertEquals(line.vendor_id, self.supplierinfo_a2.name)
        sale.action_confirm()
        self.assertEquals(
            self.supplierinfo_a2.route_ids[0], line.move_ids.rule_id.route_id)
