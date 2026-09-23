###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields
from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase


class TestSaleOrderConfirmLock(TransactionCase):

    def setUp(self):
        super().setUp()
        self.partner = self.env['res.partner'].create({
            'name': 'Test customer',
        })
        self.product = self.env['product.product'].create({
            'name': 'Test service product',
            'type': 'service',
        })
        self.route = self.env['stock.route'].search([], limit=1)
        self.order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [(0, 0, {
                'name': self.product.name,
                'product_id': self.product.id,
                'product_uom_qty': 2.0,
                'price_unit': 100.0,
            })],
        })
        self.order.action_confirm()
        self.line = self.order.order_line.filtered(
            lambda line: not line.display_type)[:1]

    def test_confirmed_order_blocks_add_line_from_order_write(self):
        with self.assertRaises(UserError):
            self.order.write({
                'order_line': [fields.Command.create({
                    'name': self.product.name,
                    'product_id': self.product.id,
                    'product_uom_qty': 1.0,
                    'price_unit': 50.0,
                })],
            })

    def test_confirmed_order_blocks_create_line_directly(self):
        with self.assertRaises(UserError):
            self.env['sale.order.line'].create({
                'name': self.product.name,
                'order_id': self.order.id,
                'product_id': self.product.id,
                'product_uom_qty': 1.0,
                'price_unit': 10.0,
            })

    def test_confirmed_order_blocks_delete_line(self):
        with self.assertRaises(UserError):
            self.line.unlink()

    def test_confirmed_order_blocks_protected_fields(self):
        protected_values = [
            {'discount': 10.0},
            {'price_unit': 80.0},
            {'product_id': self.product.id},
            {'product_uom_qty': 3.0},
            {'route_id': self.route.id},
        ]
        for values in protected_values:
            with self.subTest(values=values):
                with self.assertRaises(UserError):
                    self.line.write(values)

    def test_draft_order_allows_line_changes(self):
        order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [(0, 0, {
                'name': self.product.name,
                'product_id': self.product.id,
                'product_uom_qty': 1.0,
                'price_unit': 15.0,
            })],
        })
        line = order.order_line.filtered(
            lambda sale_line: not sale_line.display_type)[:1]
        line.write({
            'discount': 5.0,
            'price_unit': 20.0,
            'product_uom_qty': 4.0,
            'route_id': self.route.id,
        })
        self.assertEqual(line.discount, 5.0)
        self.assertEqual(line.price_unit, 20.0)
        self.assertEqual(line.product_uom_qty, 4.0)
        self.assertEqual(line.route_id, self.route)

    def test_confirmed_order_allows_non_protected_line_changes(self):
        commitment_date = fields.Datetime.now()
        self.line.write({'customer_lead': 2.0})
        self.order.write({'commitment_date': commitment_date})
        self.assertEqual(self.line.customer_lead, 2.0)
        self.assertEqual(self.order.commitment_date, commitment_date)
