###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests.common import TransactionCase


class TestSaleInvoicePolicyPartner(TransactionCase):
    def test_partner_with_invoice_policy(self):
        partner1 = self.env['res.partner'].create({
            'name': 'Partner 1 test',
            'invoice_policy': 'order',
        })
        sale = self.env['sale.order'].create({
            'partner_id': partner1.id,
        })
        self.assertFalse(sale.invoice_policy)
        sale.on_change_partner_invoice_id()
        self.assertEquals(sale.invoice_policy, 'order')

    def test_sale_with_invoice_policy(self):
        partner1 = self.env['res.partner'].create({
            'name': 'Partner 1 test',
            'invoice_policy': 'order',
        })
        sale = self.env['sale.order'].create({
            'partner_id': partner1.id,
            'invoice_policy': 'delivery',
        })
        self.assertEquals(sale.invoice_policy, 'delivery')
        sale.on_change_partner_invoice_id()
        self.assertEquals(sale.invoice_policy, 'order')

    def test_partner_without_invoice_policy(self):
        partner2 = self.env['res.partner'].create({
            'name': 'Partner 1 test',
        })
        sale = self.env['sale.order'].create({
            'partner_id': partner2.id,
        })
        self.assertFalse(sale.invoice_policy)
        sale.on_change_partner_invoice_id()
        self.assertFalse(sale.invoice_policy)
