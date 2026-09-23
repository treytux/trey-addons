###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.exceptions import ValidationError
from odoo.tests import Form
from odoo.tests.common import TransactionCase


class TestSaleOrderLineCustomerinfoSelector(TransactionCase):
    def setUp(self):
        super().setUp()
        self.partner = self.env['res.partner'].create({
            'name': 'Test Customer',
            'is_company': True,
        })
        self.other_partner = self.env['res.partner'].create({
            'name': 'Other Customer',
            'is_company': True,
        })
        self.product = self.env.ref('product.product_product_4')
        self.customerinfo_lat = self.env['product.customerinfo'].create({
            'partner_id': self.partner.id,
            'product_id': self.product.id,
            'product_code': 'LAT',
            'product_name': 'Lat Cable',
            'price': 12.5,
            'min_qty': 2.0,
            'sequence': 5,
        })
        self.customerinfo_nat = self.env['product.customerinfo'].create({
            'partner_id': self.partner.id,
            'product_id': self.product.id,
            'product_code': 'NAT',
            'product_name': 'Nat Cable',
            'price': 18.75,
            'min_qty': 4.0,
            'sequence': 10,
        })

    def _new_order_form(self):
        order_form = Form(self.env['sale.order'])
        if 'warehouse_id' in self.env['sale.order']._fields:
            order_form.warehouse_id = self.env.ref('stock.warehouse0')
        return order_form

    def test_default_customerinfo_is_selected(self):
        order_form = self._new_order_form()
        order_form.partner_id = self.partner
        with order_form.order_line.new() as line_form:
            line_form.product_id = self.product
        order = order_form.save()
        line = order.order_line[:1]
        self.assertEqual(line.customerinfo_id, self.customerinfo_lat)
        self.assertEqual(line.customerinfo_id.display_name, 'Lat Cable')
        self.assertTrue(line.name.startswith('[LAT]'))
        self.assertIn('Lat Cable', line.name)
        self.assertEqual(line.product_uom_qty, 2.0)
        self.assertEqual(line.price_unit, 12.5)

    def test_user_can_switch_customerinfo(self):
        order_form = self._new_order_form()
        order_form.partner_id = self.partner
        with order_form.order_line.new() as line_form:
            line_form.product_id = self.product
            line_form.customerinfo_id = self.customerinfo_nat
        order = order_form.save()
        line = order.order_line[:1]
        self.assertEqual(line.customerinfo_id, self.customerinfo_nat)
        self.assertEqual(line.customerinfo_id.display_name, 'Nat Cable')
        self.assertTrue(line.name.startswith('[NAT]'))
        self.assertIn('Nat Cable', line.name)
        self.assertEqual(line.product_uom_qty, 4.0)
        self.assertEqual(line.price_unit, 18.75)

    def test_customer_change_blocked_line_customerinfo_not_match(self):
        order_form = self._new_order_form()
        order_form.partner_id = self.partner
        with order_form.order_line.new() as line_form:
            line_form.product_id = self.product
            line_form.customerinfo_id = self.customerinfo_lat
        order = order_form.save()

        with self.assertRaises(ValidationError):
            order.write({
                'partner_id': self.other_partner.id,
            })
