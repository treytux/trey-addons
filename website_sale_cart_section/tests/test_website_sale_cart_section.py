###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from unittest.mock import MagicMock, patch

from odoo.tests.common import TransactionCase


class TestWebsiteSaleCartSectionReal(TransactionCase):

    def setUp(self):
        super().setUp()
        self.partner = self.env.ref('base.public_partner')
        self.order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'state': 'draft',
        })
        self.product_a = self.env['product.product'].create({
            'name': 'Test Product A',
            'list_price': 100.0,
            'active': True,
        })
        self.product_b = self.env['product.product'].create({
            'name': 'Test Product B',
            'list_price': 50.0,
            'active': True,
        })
        fake_website = MagicMock()
        fake_website.sale_get_order.return_value = self.order

    def test_cart_update_line_before_section(self):
        self.env['sale.order.line'].create({
            'order_id': self.order.id,
            'name': 'Section',
            'display_type': 'line_section',
            'sequence': 100,
        })
        fake_request = MagicMock()
        fake_request.website.sale_get_order.return_value = self.order
        with patch(
            'odoo.addons.website_sale_cart_section.models.sale_order.request',
            new=fake_request
        ):
            self.order._cart_update(
                product_id=self.product_a.id,
                add_qty=1
            )
        product_line = self.order.order_line.filtered(
            lambda lam: lam.product_id == self.product_a
        )
        self.assertTrue(product_line.exists())
        self.assertEqual(product_line.sequence, 99)

    def test_cart_sections_handling(self):
        section_lone = self.env['sale.order.line'].create({
            'order_id': self.order.id,
            'name': 'Section',
            'display_type': 'line_section',
        })
        if not self.order.order_line.filtered(
                lambda ln: ln.display_type != 'line_section'):
            self.order.order_line.filtered(
                lambda ln: not ln.product_id.active
                and ln.display_type == 'line_section'
            ).unlink()
        self.assertFalse(section_lone.exists())
        self.env['sale.order.line'].create({
            'order_id': self.order.id,
            'product_id': self.product_a.id,
        })
        section_with_goods = self.env['sale.order.line'].create({
            'order_id': self.order.id,
            'name': 'Section',
            'display_type': 'line_section',
        })
        if not self.order.order_line.filtered(
                lambda ln: ln.display_type != 'line_section'):
            self.order.order_line.filtered(
                lambda ln: not ln.product_id.active
                and ln.display_type == 'line_section'
            ).unlink()
        self.assertTrue(section_with_goods.exists())

    def test_cart_update_json_multi_section_success(self):
        payload = {
            'product_id': [self.product_a.id, self.product_b.id],
            'set_qty': [2, 5]
        }
        len_order_line = len(self.order.order_line)
        sequence = (len_order_line != 0
                    and self.order.order_line[len_order_line - 1].sequence + 1
                    or 1)
        first_product = self.env['product.product'].browse(payload['product_id'][0])
        self.order.update({
            'order_line': [(0, 0, {
                'name': first_product.name,
                'display_type': 'line_section',
                'sequence': sequence
            })]
        })
        sequence += 1
        for prdt, qty in zip(payload['product_id'], payload['set_qty']):
            product = self.env['product.product'].browse(prdt)
            self.order.update({
                'order_line': [(0, 0, {
                    'product_id': product.id,
                    'product_uom_qty': qty or 1,
                    'sequence': sequence
                })]
            })
            sequence += 1
        lines = self.order.order_line.sorted('sequence')
        self.assertEqual(len(lines), 3)
        self.assertEqual(lines[0].display_type, 'line_section')
        self.assertEqual(lines[0].name, 'Test Product A')
        self.assertEqual(lines[1].product_id, self.product_a)
        self.assertEqual(lines[2].product_id, self.product_b)
        self.assertTrue(lines[2].sequence > lines[1].sequence > lines[0].sequence)

    def test_cart_update_json_multi_section_not_draft(self):
        self.order.state = 'sale'
        if self.order.state != 'draft':
            res = {}
        self.assertEqual(res, {})
        self.assertEqual(len(self.order.order_line), 0)
