###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests import common


class TestSaleOrderCancel(common.TransactionCase):
    def setUp(self):
        super().setUp()
        self.partner = self.env.ref('base.res_partner_1')
        self.order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
        })
        self.wizard = self.env['sale.order.cancel'].create({
            'order_id': self.order.id,
        })

    def test_without_posted_invoice(self):
        self.assertFalse(self.wizard.has_posted_invoice)

    def test_with_posted_invoice(self):
        invoice = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': self.partner.id,
            'invoice_line_ids': [(0, 0, {
                'product_id': self.env.ref('product.product_product_4').id,
                'quantity': 1.0,
            })],
        })
        invoice.action_post()
        self.order.invoice_ids |= invoice
        wizard = self.env['sale.order.cancel'].create({
            'order_id': self.order.id,
        })
        self.assertTrue(wizard.has_posted_invoice)
