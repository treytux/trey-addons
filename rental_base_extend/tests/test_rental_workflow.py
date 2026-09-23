###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests.common import TransactionCase


class TestRentalWorkflow(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env['res.partner'].create({
            'name': 'Rental Customer',
        })
        cls.normal_order = cls.env['sale.order'].create({
            'partner_id': cls.partner.id,
            'type_id': cls.env.ref('sale_order_type.normal_sale_type').id,
        })
        cls.rental_order = cls.env["sale.order"].create({
            'partner_id': cls.partner.id,
            'type_id': cls.env.ref('rental_base.rental_sale_type').id,
        })

    def _new_line(self, order):
        return self.env['sale.order.line'].new({
            'order_id': order.id,
        })

    def test_rental_product_domain_is_restricted_by_default(self):
        self.env['ir.config_parameter'].sudo().set_param(
            'rental_base_extend.rental_allow_products', 'False')
        self.assertEqual(
            self._new_line(self.rental_order).rental_product_domain,
            [('rented_product_id', '!=', False)])
        self.assertEqual(
            self._new_line(self.normal_order).rental_product_domain, [])

    def test_rental_product_domain_allows_products_when_enabled(self):
        self.env['ir.config_parameter'].sudo().set_param(
            'rental_base_extend.rental_allow_products', 'True')
        self.assertEqual(
            self._new_line(self.rental_order).rental_product_domain, [])

    def test_rental_line_defaults_from_order_type(self):
        rental_line = self._new_line(self.rental_order)
        rental_line._onchange_order_id_set_rental_default()
        self.assertTrue(rental_line.rental)
        normal_line = self._new_line(self.normal_order)
        normal_line._onchange_order_id_set_rental_default()
        self.assertFalse(normal_line.rental)

    def test_sales_and_rental_actions_have_exclusive_domains(self):
        self.assertIn(
            'is_rental_order', self.env.ref('sale.action_orders').domain)
        self.assertIn(
            'is_rental_order',
            self.env.ref('rental_base.action_rental_orders').domain)
