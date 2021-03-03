###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests.common import TransactionCase


class TestAccountAccountPrivate(TransactionCase):

    def test_access_account(self):
        user = self.env['res.users'].create({
            'name': 'Test User',
            'login': 'user@test.com',
            'company_ids': [(6, 0, [self.env.user.company_id.id])],
            'company_id': self.env.user.company_id.id,
            'groups_id': [(6, 0, [
                self.env.ref('base.group_no_one').id,
                self.env.ref('account.group_account_manager').id,
            ])],
        })
        account_type = self.env.ref('account.data_account_type_receivable')
        account = self.env['account.account'].create({
            'code': '100',
            'user_type_id': account_type.id,
            'name': 'Test account',
            'reconcile': True,
        })
        journal = self.env['account.journal'].create({
            'name': 'Customer Invoices - Test',
            'code': 'TINV',
            'type': 'sale',
            'default_credit_account_id': account.id,
            'default_debit_account_id': account.id,
            'refund_sequence': True,
        })
        move = self.env['account.move'].create({
            'name': 'Test move',
            'journal_id': journal.id,
            'line_ids': [
                (0, 0, {
                    'account_id': account.id,
                    'debit': 10,
                }),
                (0, 0, {
                    'account_id': account.id,
                    'credit': 10,
                }),
            ],
        })
        move.action_post()
        account_obj = self.env['account.account'].sudo(user.id)
        move_line_obj = self.env['account.move.line'].sudo(user.id)
        account_search = move_line_obj.browse(account.id)
        self.assertEqual(len(account_search), 1)
        lines = move_line_obj.search([('account_id', '=', account.id)])
        self.assertEqual(len(lines), 2)
        account.restrict_user_ids = [(6, 0, [user.id])]
        account_search = account_obj.browse(account.id)
        self.assertEqual(len(account_search), 1)
        lines = move_line_obj.search([('account_id', '=', account.id)])
        self.assertEqual(len(lines), 2)
        account.restrict_user_ids = [(6, 0, [self.env.user.id])]
        account_search = account_obj.browse(account.id)
        self.assertEqual(len(account_search), 0)
        lines = move_line_obj.search([('account_id', '=', account.id)])
        self.assertEqual(len(lines), 0)
