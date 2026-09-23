###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests.common import TransactionCase


class TestSaleInvoicePolicyPartner(TransactionCase):
    def test_partner_with_invoice_policy(self):
        partner1 = self.env['res.partner'].create({
            'name': 'Partner 1 test',
            'invoice_policy': 'delivery',
        })
        sale = self.env['sale.order'].create({
            'partner_id': partner1.id,
        })
        self.assertEqual(sale.invoice_policy, 'delivery')

    def test_sale_with_invoice_policy(self):
        partner2 = self.env['res.partner'].create({
            'name': 'Partner 2 test',
            'invoice_policy': 'order',
        })
        sale = self.env['sale.order'].create({
            'partner_id': partner2.id,
            'invoice_policy': 'delivery',
        })
        self.assertEqual(sale.invoice_policy, 'order')

    def test_partner_without_invoice_policy(self):
        partner3 = self.env['res.partner'].create({
            'name': 'Partner 3 test',
        })
        sale = self.env['sale.order'].create({
            'partner_id': partner3.id,
        })
        self.assertEqual(sale.invoice_policy, 'order')

    def test_change_invoice_policy(self):
        partner_delivery = self.env['res.partner'].create({
            'name': 'Test invoice policy delivery',
            'invoice_policy': 'delivery',
        })
        partner_order = self.env['res.partner'].create({
            'name': 'Test invoice policy order',
            'invoice_policy': 'order',
        })
        sale = self.env['sale.order'].create({
            'partner_id': partner_order.id,
        })
        self.assertEqual(sale.invoice_policy, 'order')
        sale.partner_id = partner_delivery
        self.assertEqual(sale.invoice_policy, 'delivery')
        sale.invoice_policy = 'order'
        self.assertEqual(sale.invoice_policy, 'order')
        sale.partner_id = partner_delivery
        self.assertEqual(sale.invoice_policy, 'delivery')
