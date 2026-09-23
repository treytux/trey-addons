###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests import TransactionCase


class TestAccountMoveUnpaidReminder(TransactionCase):

    def setUp(self):
        super().setUp()
        self.sale_installed = self.env['ir.module.module'].search([
            ('name', '=', 'sale'),
            ('state', '=', 'installed'),
        ])
        self.partner = self.env['res.partner'].create({
            'name': 'Test Partner',
        })
        self.product = self.env['product.product'].create({
            'name': 'Test Service',
            'type': 'service',
        })
        self.template = self.env.ref(
            'account_move_unpaid_reminder.email_tmpl_unpaid_reminder')

    def test_create_invoice_minimum(self):
        if not self.sale_installed:
            self.skipTest('sale module not installed')
        invoice = self.env['account.move'].create({
            'partner_id': self.partner.id,
            'move_type': 'out_invoice',
            'invoice_line_ids': [(0, 0, {
                'product_id': self.product.id,
                'quantity': 1,
                'price_unit': 100,
            })],
            'unpaid_reminder': True,
        })
        self.assertTrue(invoice.unpaid_reminder)

    def test_create_invoice_defaults(self):
        if not self.sale_installed:
            self.skipTest('sale module not installed')
        invoice = self.env['account.move'].create({
            'partner_id': self.partner.id,
            'move_type': 'out_invoice',
            'invoice_line_ids': [(0, 0, {
                'product_id': self.product.id,
                'quantity': 1,
                'price_unit': 100,
            })],
        })
        self.assertFalse(invoice.unpaid_reminder)
        self.assertEqual(invoice.state, 'draft')
        self.assertEqual(invoice.payment_state, 'not_paid')
