###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests import common


class TestFieldserviceSaleOrderLink(common.TransactionCase):

    def setUp(self):
        super().setUp()
        self.partner = self.env['res.partner'].create({
            'name': 'Partner test',
            'email': 'customer@customer.com',
            'customer': True,
        })
        self.location = self.env['fsm.location'].create({
            'name': 'Location test',
            'owner_id': self.partner.id,
            'contact_id': self.partner.id,
        })
        self.product = self.env['product.product'].create({
            'name': 'Test Product',
            'lst_price': 280.0,
        })

    def test_link_fieldservice_location_sale_order(self):
        self.assertFalse(self.location.sale_order_ids)
        sale1 = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'fsm_location_id': self.location.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product.id,
                    'price_unit': 100,
                    'product_uom_qty': 1}),
            ]
        })
        sale1.action_confirm()
        self.assertEquals(sale1.fsm_location_id, self.location)
        self.assertEquals(len(self.location.sale_order_ids), 1)
        self.assertIn(sale1, self.location.sale_order_ids)
        sale2 = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'fsm_location_id': self.location.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product.id,
                    'price_unit': 100,
                    'product_uom_qty': 1}),
            ]
        })
        sale2.action_confirm()
        self.assertEquals(sale2.fsm_location_id, self.location)
        self.assertEquals(len(self.location.sale_order_ids), 2)
        self.assertIn(sale2.id, self.location.sale_order_ids.ids)
