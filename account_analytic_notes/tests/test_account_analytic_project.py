###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests.common import TransactionCase


class TestAccountAnalyticNotes(TransactionCase):

    def setUp(self):
        super(TestAccountAnalyticNotes, self).setUp()

    def test_account_analytic_notes(self):
        data = {
            'type': 'contract',
            'state': 'open',
            'name': 'Account analytic account test',
            'notes': 'Account analytic account notes'}
        contract_test = self.env['account.analytic.account'].create(data)
        self.assertEquals(
            contract_test.notes, 'Account analytic account notes')
