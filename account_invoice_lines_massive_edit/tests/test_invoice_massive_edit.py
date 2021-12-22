###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests import common


class TestInvoiceMassiveEdit(common.TransactionCase):

    def setUp(self):
        super(TestInvoiceMassiveEdit, self).setUp()

    def test_update_invoice(self):
        """ Update Invoice"""
        partner = self.env['res.partner'].create({
            'name': 'Partner for test module '
                    'account_invoice_lines_massive_edit',
            'customer': True})
        # Create analytic journal
        journal = self.env['account.journal'].create({
            'name': 'Journal for test module '
                    'account_invoice_lines_massive_edit',
            'type': 'general',
            'code': 'XXX',
            'company_id': self.env.user.company_id.id})
        # Create analytic account
        account = self.env['account.analytic.account'].create({
            'name': 'Account for test module '
                    'account_invoice_lines_massive_edit',
            'partner_id': partner.id,
            'company_id': self.env.user.company_id.id})
        # Search financial account por test
        invoice = self.env['account.invoice'].create({
            'partner_id': partner.id,
            'journal_id': journal.id})
        # Create analytic line for invoice
        for i in range(1, 10):
            self.env['account.invoice.line'].create({
                'invoice_id': invoice.id,
                'name': 'Line for test module '
                        'account_invoice_lines_massive_edit',
                'account_id': account.id,
                'price_unit': 11.11 * i,
                'discount': 11.11 * i})
        invoice.action_lines_massive_edit()
