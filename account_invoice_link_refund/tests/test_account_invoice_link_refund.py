###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests import common


class TestAccountInvoiceLinkRefund(common.TransactionCase):

    def setUp(self):
        super().setUp()
        self.partner = self.env['res.partner'].create({
            'name': 'Partner test',
        })
        default_line_account = self.env['account.account'].search([
            ('internal_type', '=', 'other'),
            ('deprecated', '=', False),
            ('company_id', '=', self.env.user.company_id.id),
        ], limit=1)
        self.invoice_lines = [
            (0, False, {
                'name': 'Account line test 1',
                'account_id': default_line_account.id,
                'quantity': 1.0,
                'price_unit': 10.0,
            }),
            (0, False, {
                'name': 'Account line test 2',
                'account_id': default_line_account.id,
                'quantity': 2.0,
                'price_unit': 15.0,
            }),
        ]
        self.invoice = self.env['account.invoice'].create({
            'partner_id': self.partner.id,
            'type': 'out_invoice',
            'invoice_line_ids': self.invoice_lines,
        })
        self.invoice.action_invoice_open()
        self.env['account.invoice.refund'].with_context(
            active_ids=self.invoice.ids).create({
                'filter_refund': 'refund',
                'description': 'Refund reason',
            }).invoice_refund()

    def test_create_invoice_refund_and_check_link_account_invoice(self):
        self.assertTrue(self.invoice.refund_invoice_ids)
        refund = self.invoice.refund_invoice_ids[0]
        self.assertTrue(refund.invoices_related_ids)
        self.assertEqual(len(refund.invoices_related_ids), 1)
        self.assertEqual(
            refund.invoices_related_ids[0].number, self.invoice.number)
        self.assertEqual(
            refund.invoices_related_ids[0].reference, self.invoice.reference)
        self.assertEqual(
            refund.invoices_related_ids[0].partner_id, self.invoice.partner_id)
        self.assertEqual(
            refund.invoices_related_ids[0].date_invoice,
            self.invoice.date_invoice)
        self.assertEqual(
            refund.invoices_related_ids[0].origin, self.invoice.origin)
        self.assertEqual(
            refund.invoices_related_ids[0].amount_total,
            self.invoice.amount_total)
        self.assertEqual(
            refund.invoices_related_ids[0].state, self.invoice.state)
        self.assertEqual(refund.invoices_related_ids[0].id, self.invoice.id)
