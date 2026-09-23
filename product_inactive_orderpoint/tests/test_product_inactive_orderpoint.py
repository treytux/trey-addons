###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase


class TestProductInactiveOrderpoint(TransactionCase):
    def setUp(self):
        super().setUp()
        self.product_01 = self.env['product.product'].create({
            'type': 'product',
            'company_id': False,
            'name': 'Test product 1',
            'standard_price': 10,
            'list_price': 100,
        })
        attr = self.env['product.attribute'].create({
            'name': 'Attribute test',
        })
        for value in ['A', 'B', 'C']:
            self.env['product.attribute.value'].create({
                'attribute_id': attr.id,
                'name': value,
            })
        self.template_02 = self.env['product.template'].create({
            'name': 'Test product 2',
            'type': 'product',
            'standard_price': 10.00,
            'attribute_line_ids': [
                (0, 0, {
                    'attribute_id': attr.id,
                    'value_ids': [(6, 0, attr.value_ids.ids)],
                }),
            ],
        })
        self.warehouse = self.env.ref('stock.warehouse0')
        self.env['stock.warehouse.orderpoint'].create({
            'name': ('Orderpoint Test %s') % self.product_01.id,
            'warehouse_id': self.warehouse.id,
            'location_id': self.warehouse.lot_stock_id.id,
            'product_id': self.product_01.id,
            'product_min_qty': 25.00,
            'product_max_qty': 50.00,
            'company_id': self.env.user.company_id.id,
        })
        self.assertEquals(len(self.template_02.product_variant_ids), 3)

    def test_template_inactive_orderpoint(self):
        self.assertTrue(self.product_01.product_tmpl_id.active)
        self.assertTrue(self.product_01.active)
        self.assertTrue(self.product_01.orderpoint_ids)
        self.product_01.product_tmpl_id.product_inactive_orderpoint()
        self.assertFalse(self.product_01.product_tmpl_id.active)
        self.assertFalse(self.product_01.active)
        self.assertFalse(self.product_01.orderpoint_ids)

    def test_product_inactive_orderpoint(self):
        self.assertTrue(self.product_01.product_tmpl_id.active)
        self.assertTrue(self.product_01.active)
        self.assertTrue(self.product_01.orderpoint_ids)
        self.product_01.product_inactive_orderpoint()
        self.assertTrue(self.product_01.product_tmpl_id.active)
        self.assertFalse(self.product_01.active)
        self.assertFalse(self.product_01.orderpoint_ids)

    def test_default_inactive_template(self):
        self.assertTrue(self.product_01.product_tmpl_id.active)
        self.assertTrue(self.product_01.active)
        self.assertTrue(self.product_01.orderpoint_ids)
        with self.assertRaises(UserError) as result:
            self.product_01.product_tmpl_id.toggle_active()
        self.assertIn(
            'You still have some active reordering rules on this product. '
            'Please archive or delete them first.', result.exception.name)
        self.assertFalse(self.product_01.product_tmpl_id.active)
        self.assertFalse(self.product_01.active)
        self.assertTrue(self.product_01.orderpoint_ids)

    def test_default_inactive_product(self):
        self.assertTrue(self.product_01.product_tmpl_id.active)
        self.assertTrue(self.product_01.active)
        self.assertTrue(self.product_01.orderpoint_ids)
        with self.assertRaises(UserError) as result:
            self.product_01.toggle_active()
        self.assertIn(
            'You still have some active reordering rules on this product. '
            'Please archive or delete them first.', result.exception.name)
        self.assertTrue(self.product_01.product_tmpl_id.active)
        self.assertFalse(self.product_01.active)
        self.assertTrue(self.product_01.orderpoint_ids)

    def test_product_inactive_orderpoint_variants(self):
        self.assertTrue(self.template_02.active)
        self.assertEquals(len(self.template_02.product_variant_ids), 3)
        self.assertTrue(self.template_02.product_variant_ids.mapped('active'))
        product_variant_1 = self.template_02.product_variant_ids[0]
        self.env['stock.warehouse.orderpoint'].create({
            'name': ('Orderpoint Test %s') % product_variant_1.id,
            'warehouse_id': self.warehouse.id,
            'location_id': self.warehouse.lot_stock_id.id,
            'product_id': product_variant_1.id,
            'product_min_qty': 25.00,
            'product_max_qty': 50.00,
            'company_id': self.env.user.company_id.id,
        })
        self.assertTrue(product_variant_1.orderpoint_ids)
        self.template_02.product_variant_ids.product_inactive_orderpoint()
        self.assertFalse(self.template_02.product_variant_ids.mapped('active'))
        self.assertFalse(product_variant_1.orderpoint_ids)
        self.assertEquals(len(self.template_02.product_variant_ids), 0)
        self.assertTrue(self.template_02.active)

    def test_template_inactive_orderpoint_with_variants(self):
        self.assertTrue(self.template_02.active)
        self.assertEquals(len(self.template_02.product_variant_ids), 3)
        product_variant_1 = self.template_02.product_variant_ids[0]
        self.assertTrue(self.template_02.product_variant_ids.mapped('active'))
        self.env['stock.warehouse.orderpoint'].create({
            'name': ('Orderpoint Test %s') % product_variant_1.id,
            'warehouse_id': self.warehouse.id,
            'location_id': self.warehouse.lot_stock_id.id,
            'product_id': product_variant_1.id,
            'product_min_qty': 25.00,
            'product_max_qty': 50.00,
            'company_id': self.env.user.company_id.id,
        })
        self.assertTrue(product_variant_1.orderpoint_ids)
        self.template_02.product_inactive_orderpoint()
        self.assertFalse(self.template_02.product_variant_ids.mapped('active'))
        self.assertFalse(product_variant_1.orderpoint_ids)
        self.assertEquals(len(self.template_02.product_variant_ids), 0)
        self.assertFalse(self.template_02.active)
