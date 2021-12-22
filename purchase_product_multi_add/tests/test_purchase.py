###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import odoo.tests.common as common


class TestSale(common.TransactionCase):

    def setUp(self):
        super(TestSale, self).setUp()
        self.product_9 = self.env.ref('product.product_product_9')
        self.product_11 = self.env.ref('product.product_product_11')

    def test_import_product(self):
        po = self.env['purchase.order'].create({
            'partner_id': self.env.ref('base.res_partner_2').id,
        })
        wizard = self.env['purchase.import.products'].with_context(
            active_id=po.id, active_model='purchase.order')
        wizard = wizard.create({
            'products': [(6, 0, [self.product_9.id, self.product_11.id])],
        })
        wizard.create_items()
        wizard.items[0].quantity = 4
        wizard.items[1].quantity = 6
        wizard.select_products()
        self.assertEqual(len(po.order_line), 2)
        for line in po.order_line:
            if line.product_id.id == self.product_9.id:
                self.assertEqual(line.product_uom_qty, 4)
            else:
                self.assertEqual(line.product_uom_qty, 6)
