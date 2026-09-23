###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests.common import TransactionCase


class TestPrintOptionsInvoice(TransactionCase):

    def setUp(self):
        super().setUp()
        self.partner = self.env['res.partner'].create({
            'name': 'Print Options Invoice Test Partner',
        })
        self.move = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': self.partner.id,
        })

    def test_action_print_options_invoice_opens_wizard(self):
        action = self.move.action_print_options_invoice()
        self.assertEqual(action['res_model'], 'wiz.print.options.invoice')
        self.assertEqual(action['target'], 'new')

    def test_button_print_with_payments(self):
        wiz = self.env['wiz.print.options.invoice'].with_context(
            active_ids=self.move.ids).create({
                'print_option': 'with_payments',
            })
        action = wiz.button_print()
        self.assertEqual(
            action['report_name'], 'account.report_invoice_with_payments')

    def test_button_print_without_payments(self):
        wiz = self.env['wiz.print.options.invoice'].with_context(
            active_ids=self.move.ids).create({
                'print_option': 'without_payments',
            })
        action = wiz.button_print()
        self.assertEqual(action['report_name'], 'account.report_invoice')
