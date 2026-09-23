###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests import TransactionCase


class TestCronObsolete(TransactionCase):

    def setUp(self):
        super().setUp()
        self.product = self.env['product.product'].create({
            'type': 'product',
            'company_id': False,
            'name': 'Test product',
            'standard_price': 10,
            'list_price': 100,
        })
        self.stock_location = self.env.ref('stock.stock_location_stock')

    def update_qty_on_hand(self, product, new_qty):
        wizard = self.env['stock.change.product.qty'].create({
            'product_id': product.id,
            'new_quantity': new_qty,
            'location_id': self.stock_location.id,
        })
        wizard.change_product_qty()

    def test_archive_obsolete_without_stock(self):
        self.product.is_obsolete = True
        self.update_qty_on_hand(self.product, 10)
        self.env[
            'product.product'].cron_archive_obsolete_products_without_stock()
        self.assertTrue(self.product.active)
        self.assertTrue(self.product.product_tmpl_id.active)
        self.update_qty_on_hand(self.product, 0)
        self.env[
            'product.product'].cron_archive_obsolete_products_without_stock()
        self.assertFalse(self.product.active)
        self.assertFalse(self.product.product_tmpl_id.active)

    def test_archive_obsolete_without_stock_multi_variant(self):
        attr = self.env['product.attribute'].create({
            'name': 'Size',
        })
        val_a = self.env['product.attribute.value'].create({
            'attribute_id': attr.id, 'name': 'A',
        })
        val_b = self.env['product.attribute.value'].create({
            'attribute_id': attr.id, 'name': 'B',
        })
        tmpl = self.env['product.template'].create({
            'type': 'product', 'company_id': False, 'name': 'Multi',
            'attribute_line_ids': [(0, 0, {
                'attribute_id': attr.id,
                'value_ids': [(6, 0, (val_a + val_b).ids)],
            })],
        })
        var_a = tmpl.product_variant_ids.filtered(
            lambda p: p.attribute_value_ids.name == 'A')
        var_b = tmpl.product_variant_ids.filtered(
            lambda p: p.attribute_value_ids.name == 'B')
        var_a.is_obsolete = True
        self.env[
            'product.product'].cron_archive_obsolete_products_without_stock()
        self.assertFalse(var_a.active)
        self.assertTrue(var_b.active)
        self.assertTrue(tmpl.active)

    def test_archive_obsolete_multi_variant_full_template(self):
        attr = self.env['product.attribute'].create({
            'name': 'Color',
        })
        val_red = self.env['product.attribute.value'].create({
            'attribute_id': attr.id,
            'name': 'Red',
        })
        val_blue = self.env['product.attribute.value'].create({
            'attribute_id': attr.id,
            'name': 'Blue',
        })
        tmpl = self.env['product.template'].create({
            'type': 'product', 'company_id': False, 'name': 'Full template',
            'attribute_line_ids': [(0, 0, {
                'attribute_id': attr.id,
                'value_ids': [(6, 0, (val_red + val_blue).ids)],
            })],
        })
        var_red = tmpl.product_variant_ids.filtered(
            lambda p: p.attribute_value_ids.name == 'Red')
        var_blue = tmpl.product_variant_ids.filtered(
            lambda p: p.attribute_value_ids.name == 'Blue')
        tmpl.is_obsolete = True
        self.assertTrue(var_red.is_obsolete)
        self.assertTrue(var_blue.is_obsolete)
        self.env[
            'product.product'].cron_archive_obsolete_products_without_stock()
        self.assertFalse(var_red.active)
        self.assertFalse(var_blue.active)
        self.assertFalse(tmpl.active)

    def test_archive_obsolete_with_orderpoint(self):
        self.product.is_obsolete = True
        self.update_qty_on_hand(self.product, 0)
        orderpoint = self.env['stock.warehouse.orderpoint'].create({
            'product_id': self.product.id,
            'product_min_qty': 10,
            'product_max_qty': 100,
        })
        self.assertTrue(orderpoint.active)
        self.env[
            'product.product'].cron_archive_obsolete_products_without_stock()
        self.assertFalse(orderpoint.active)
        self.assertFalse(self.product.active)
        self.assertFalse(self.product.product_tmpl_id.active)
