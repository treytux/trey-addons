###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import exceptions
from odoo.tests.common import TransactionCase


class TestAccountMovePrintLine(TransactionCase):

    def setUp(self):
        super().setUp()
        self.partner = self.env['res.partner'].create({
            'name': 'Partner test',
        })
        self.product = self.env['product.product'].search([], limit=1)
        self.tax = self.env['account.tax'].create({
            'name': 'Tax 21%',
            'amount_type': 'percent',
            'amount': 21,
            'type_tax_use': 'sale',
        })
        self.move = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': self.partner.id,
            'invoice_line_ids': [
                (0, 0, {
                    'product_id': self.product.id,
                    'name': self.product.name,
                    'price_unit': 100,
                    'quantity': 3,
                    'discount': 10,
                    'tax_ids': [(6, 0, self.tax.ids)],
                }),
            ],
        })

    def test_action_print_line_copy_matches_real_totals(self):
        self.move.action_print_line_copy()
        self.assertEqual(len(self.move.print_line_ids), 1)
        self.assertAlmostEqual(
            self.move.print_line_untaxed, self.move.amount_untaxed)
        self.assertAlmostEqual(
            self.move.print_line_tax, self.move.amount_tax)
        self.assertAlmostEqual(
            self.move.print_line_total, self.move.amount_total)
        self.move.print_line = True

    def test_check_print_lines_raises_on_mismatch(self):
        self.env['account.move.print.line'].create({
            'move_id': self.move.id,
            'name': 'Wrong amount line',
            'quantity': 1,
            'price_unit': 1,
        })
        with self.assertRaises(exceptions.UserError):
            self.move.print_line = True

    def test_report_renders_with_and_without_print_line(self):
        report = self.env.ref('account.account_invoices')
        report._render_qweb_html(
            'account.account_invoices', self.move.ids)
        self.move.action_print_line_copy()
        self.move.print_line = True
        report._render_qweb_html(
            'account.account_invoices', self.move.ids)
