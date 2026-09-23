###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests import common


class TestPurchaseOrderLinesByRef(common.TransactionCase):

    def setUp(self):
        super().setUp()
        self.partner = self.env['res.partner'].create({
            'name': 'Test partner',
            'is_company': True,
        })
        self.product_1 = self.env['product.product'].create({
            'type': 'service',
            'purchase_ok': True,
            'name': 'One',
            'list_price': 10,
            'default_code': 'R1',
        })
        self.product_2 = self.env['product.product'].create({
            'type': 'service',
            'purchase_ok': True,
            'name': 'Two',
            'list_price': 20,
            'default_code': 'R2',
            'barcode': '0123456789104',
        })

    def create_wizard(self, purchase, refs):
        return self.env['purchase.order.lines_by_ref'].create({
            'purchase_id': purchase.id,
            'references': refs,
        })

    def test_purchase_order_supplierinfo_01(self):
        self.env['product.supplierinfo'].create({
            'product_id': self.product_1.id,
            'partner_id': self.partner.id,
            'product_code': '2323',
            'price': 25,
        })
        purchase = self.env['purchase.order'].create({
            'partner_id': self.partner.id,
        })
        wizard = self.create_wizard(purchase, '\n'.join(['2323']))
        wizard.action_simulate()
        self.assertEqual(len(wizard.line_ids), 0)
        wizard.action_create()
        self.assertEqual(len(purchase.order_line), 1)
        line = purchase.order_line[0]
        self.assertEqual(line.product_id, self.product_1)
        self.assertEqual(line.product_uom_qty, 1)
        self.assertEqual(line.price_unit, 25)

    def test_purchase_order_supplierinfo_02(self):
        self.env['product.supplierinfo'].create({
            'product_id': self.product_1.id,
            'partner_id': self.partner.id,
            'product_code': '2323',
            'price': 25,
        })
        purchase = self.env['purchase.order'].create({
            'partner_id': self.partner.id,
        })
        wizard = self.create_wizard(purchase, '\n'.join(['2323/5']))
        wizard.action_simulate()
        self.assertEqual(len(wizard.line_ids), 0)
        wizard.action_create()
        self.assertEqual(len(purchase.order_line), 1)
        line = purchase.order_line[0]
        self.assertEqual(line.product_id, self.product_1)
        self.assertEqual(line.product_uom_qty, 5)
        self.assertEqual(line.price_unit, 25)

    def test_purchase_order_supplierinfo_03(self):
        self.env['product.supplierinfo'].create({
            'product_id': self.product_1.id,
            'partner_id': self.partner.id,
            'product_code': '2323',
            'price': 25,
        })
        purchase = self.env['purchase.order'].create({
            'partner_id': self.partner.id,
        })
        wizard = self.create_wizard(purchase, '\n'.join(['2323/5/15.0']))
        wizard.action_simulate()
        self.assertEqual(len(wizard.line_ids), 0)
        wizard.action_create()
        self.assertEqual(len(purchase.order_line), 1)
        line = purchase.order_line[0]
        self.assertEqual(line.product_id, self.product_1)
        self.assertEqual(line.product_uom_qty, 5)
        self.assertEqual(line.price_unit, 15)

    def test_purchase_order_supplierinfo_04(self):
        self.env['product.supplierinfo'].create({
            'product_id': self.product_1.id,
            'partner_id': self.partner.id,
            'price': 6,
        })
        purchase = self.env['purchase.order'].create({
            'partner_id': self.partner.id,
        })
        wizard = self.create_wizard(purchase, '\n'.join(['R1/5']))
        wizard.action_simulate()
        self.assertEqual(len(wizard.line_ids), 0)
        wizard.action_create()
        self.assertEqual(len(purchase.order_line), 1)
        line = purchase.order_line[0]
        self.assertEqual(line.product_id, self.product_1)
        self.assertEqual(line.product_uom_qty, 5)
        self.assertEqual(line.price_unit, 6)

    def test_purchase_order(self):
        purchase = self.env['purchase.order'].create({
            'partner_id': self.partner.id,
        })
        wizard = self.create_wizard(purchase, '\n'.join(['R1/10/30.10']))
        wizard.action_simulate()
        self.assertEqual(len(wizard.line_ids), 0)
        wizard.action_create()
        self.assertEqual(len(purchase.order_line), 1)
        line = purchase.order_line[0]
        self.assertEqual(line.product_id, self.product_1)
        self.assertEqual(line.product_uom_qty, 10)
        self.assertEqual(line.price_unit, 30.10)
        purchase.order_line.unlink()
        self.assertEqual(len(purchase.order_line), 0)
        wizard = self.create_wizard(
            purchase, '\n'.join(['0123456789104/10/20']))
        wizard.action_simulate()
        self.assertEqual(len(wizard.line_ids), 0)
        wizard.action_create()
        line = purchase.order_line[0]
        self.assertEqual(len(purchase.order_line), 1)
        self.assertEqual(line.product_id, self.product_2)
        self.assertEqual(line.product_uom_qty, 10)
        self.assertEqual(line.price_unit, 20)
        purchase.order_line.unlink()
        wizard = self.create_wizard(purchase, '\n'.join(['R1', 'R2']))
        wizard.action_simulate()
        self.assertEqual(len(wizard.line_ids), 0)
        wizard.action_create()
        self.assertEqual(len(purchase.order_line), 2)

    def test_purchase_order_with_errors(self):
        purchase = self.env['purchase.order'].create({
            'partner_id': self.partner.id,
        })
        wizard = self.create_wizard(purchase, 'RXXX/10/30.10')
        wizard.action_simulate()
        self.assertEqual(len(wizard.line_ids), 1)
        self.assertEqual('Ref not exists', wizard.line_ids.name)
        wizard.action_create()
        self.assertEqual(len(purchase.order_line), 0)

    def test_change_glue_char(self):
        set_param = self.env['ir.config_parameter'].sudo().set_param
        set_param('purchase_order_lines_by_ref.glue', ',')
        purchase = self.env['purchase.order'].create({
            'partner_id': self.partner.id,
        })
        wizard = self.create_wizard(purchase, 'R1,10,30.10')
        wizard.action_simulate()
        self.assertEqual(len(wizard.line_ids), 0)
        wizard.action_create()
        self.assertEqual(len(purchase.order_line), 1)

    def test_ref_not_for_purchase(self):
        purchase = self.env['purchase.order'].create({
            'partner_id': self.partner.id,
        })
        self.product_1.purchase_ok = False
        wizard = self.create_wizard(purchase, 'R1')
        wizard.action_simulate()
        self.assertEqual(len(wizard.line_ids), 1)
        self.assertEqual('Ref not exists', wizard.line_ids.name)
        wizard.action_create()
        self.assertEqual(len(purchase.order_line), 0)

    def test_purchase_order_supplierinfo_cod(self):
        self.env['product.supplierinfo'].create({
            'product_id': self.product_1.id,
            'partner_id': self.partner.id,
            'product_code': '',
            'price': 20,
        })
        purchase = self.env['purchase.order'].create({
            'partner_id': self.partner.id,
        })
        wizard = self.create_wizard(purchase, 'test')
        wizard.action_simulate()
        self.assertEqual(len(wizard.line_ids), 1)
        self.assertIn('Ref not exists', wizard.line_ids.name)
