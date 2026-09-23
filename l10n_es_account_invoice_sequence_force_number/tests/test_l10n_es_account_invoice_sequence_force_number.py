###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests.common import TransactionCase


class TestL10nEsAccountInvoiceSequenceForceNumber(TransactionCase):

    def setUp(self):
        super().setUp()

    def test_force_number(self):
        invoice_vals = [
            (0, 0, {
                'product_id': self.env.ref('product.product_product_3').id,
                'quantity': 1.0,
                'account_id': self.env['account.account'].search([
                    ('user_type_id', '=', self.env.ref(
                        'account.data_account_type_revenue').id),
                ], limit=1).id,
                'name': '[PCSC234] PC Assemble SC234',
                'price_unit': 450.00
            })
        ]
        invoice = self.env['account.invoice'].create({
            'name': 'Test Customer Invoice',
            'journal_id': self.env['account.journal'].search(
                [('type', '=', 'sale')], limit=1).id,
            'partner_id': self.env.ref('base.res_partner_12').id,
            'account_id': self.env['account.account'].search(
                [('user_type_id', '=', self.env.ref(
                    'account.data_account_type_receivable').id)],
                limit=1).id,
            'invoice_line_ids': invoice_vals,
        })
        invoice.move_name = '0001'
        invoice.action_invoice_open()
        self.assertEqual(invoice.number, invoice.move_name, msg='Wrong number')
        self.assertEqual(invoice.number, '0001')
