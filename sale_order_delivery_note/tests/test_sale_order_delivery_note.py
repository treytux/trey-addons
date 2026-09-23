###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests import common


class TestSaleOrderDeliveryNote(common.TransactionCase):

    def setUp(self):
        super().setUp()
        self.partner = self.env['res.partner'].create({
            'name': 'Test partner',
            'is_company': True,
        })
        self.product = self.env['product.product'].create({
            'type': 'consu',
            'company_id': False,
            'name': 'Product test',
            'standard_price': 10,
            'list_price': 30,
            'default_code': 'PR-TEST',
        })
        self.sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product.id,
                    'price_unit': self.product.list_price,
                    'product_uom_qty': 1,
                }),
            ],
        })

    def test_sale_with_delivery_note(self):
        self.assertEqual(self.sale.state, 'draft')
        self.assertFalse(self.sale.delivery_note)
        msg_delivery_note = 'Delivery note for sale order in test'
        self.sale.delivery_note = msg_delivery_note
        self.sale.action_confirm()
        self.assertEqual(self.sale.state, 'sale')
        self.assertEqual(len(self.sale.picking_ids), 1)
        picking = self.sale.picking_ids[0]
        self.assertEqual(picking.delivery_note, self.sale.delivery_note)
        self.assertEqual(picking.delivery_note, msg_delivery_note)
