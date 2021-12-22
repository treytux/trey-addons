###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests import common


class TestNotificationsSettingsSale(common.TransactionCase):

    def setUp(self):
        super().setUp()
        self.partner = self.env['res.partner'].create({
            'name': 'Test partner',
            'is_company': True,
        })
        self.product = self.env['product.product'].create({
            'name': 'Test product',
            'list_price': 10,
        })
        self.sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product.id,
                    'price_unit': 100,
                    'product_uom_qty': 1,
                }),
            ]
        })
        website = self.env['website'].create({
            'name': 'new website',
        })
        self.sale.website_id = website

    def test_notify_sale_order_confirm(self):
        for message in self.sale.message_ids:
            self.assertNotIn('Quotation', message.body)
        self.sale.website_id.notify_sale = True
        message_ids_tam = len(self.sale.message_ids)
        self.sale.action_confirm()
        last_message = self.sale.message_ids[0]
        self.assertIn('Order', last_message.subject)
        self.assertNotEqual(message_ids_tam, len(self.sale.message_ids))

    def test_notify_sale_order_cancel(self):
        self.sale.website_id.notify_cancel = True
        self.sale.action_confirm()
        message_ids_tam = len(self.sale.message_ids)
        self.sale.action_cancel()
        last_message = self.sale.message_ids[0]
        self.assertIn('has been canceled.', last_message.body)
        self.assertNotEqual(message_ids_tam, len(self.sale.message_ids))

    def test_notify_sale_order_blocked(self):
        self.sale.website_id.notify_done = True
        self.sale.action_confirm()
        message_ids_tam = len(self.sale.message_ids)
        self.sale.action_done()
        last_message = self.sale.message_ids[0]
        self.assertIn('has been blocked.', last_message.body)
        self.assertNotEqual(message_ids_tam, len(self.sale.message_ids))
