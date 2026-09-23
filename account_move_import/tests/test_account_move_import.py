###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import base64
from unittest.mock import patch

from odoo import exceptions, fields
from odoo.tests import common


class TestAccountMoveImport(common.TransactionCase):

    def setUp(self):
        super().setUp()
        self.journal = self.env['account.journal'].create({
            'name': 'Import Journal',
            'type': 'sale',
            'code': 'IMPT',
        })
        self.accounts = self.env['account.account'].search([
            ('company_id', '=', self.env.company.id),
            ('deprecated', '=', False),
        ], limit=2)
        credit_account = self.accounts[1] if len(self.accounts) > 1 \
            else self.accounts[0]
        self.move_1 = self.env['account.move'].create({
            'date': fields.Date.today(),
            'journal_id': self.journal.id,
            'line_ids': [
                (0, 0, {
                    'name': 'Move A',
                    'account_id': self.accounts[0].id,
                    'debit': 100.0,
                    'credit': 0.0,
                }),
                (0, 0, {
                    'name': 'Move A',
                    'account_id': credit_account.id,
                    'debit': 0.0,
                    'credit': 100.0,
                }),
            ],
        })
        self.move_2 = self.env['account.move'].create({
            'date': fields.Date.today(),
            'journal_id': self.journal.id,
            'line_ids': [
                (0, 0, {
                    'name': 'Move B',
                    'account_id': self.accounts[0].id,
                    'debit': 100.0,
                    'credit': 0.0,
                }),
                (0, 0, {
                    'name': 'Move B',
                    'account_id': credit_account.id,
                    'debit': 0.0,
                    'credit': 100.0,
                }),
            ],
        })

    def _new_wizard(self, file_content=b'', filename='test.txt'):
        return self.env['account.move.import_file'].with_context({
            'active_model': 'account.journal',
            'active_ids': [self.journal.id],
        }).new({
            'file': base64.b64encode(file_content),
            'filename': filename,
        })

    def test_get_file_content_decodes_utf8(self):
        wizard = self._new_wizard('Import text'.encode('utf-8'))
        self.assertEqual(wizard.get_file_content(), 'Import text')

    def test_get_file_content_falls_back_to_latin_1(self):
        wizard = self._new_wizard(b'Li\xf1a')
        self.assertEqual(wizard.get_file_content(), 'Li' + chr(241) + 'a')

    def test_import_file_none_raises_user_error(self):
        wizard = self._new_wizard(b'content')
        with self.assertRaises(exceptions.UserError) as error:
            wizard._import_file_none(self.journal, 'content')
        self.assertEqual(
            str(error.exception),
            'The type of file to import has not been defined.',
        )

    def test_import_file_dispatches_to_none_handler(self):
        wizard = self._new_wizard(b'payload')
        expected_moves = self.move_1 | self.move_2

        def _fake_import(model, journal, content):
            self.assertEqual(model, wizard)
            self.assertEqual(journal, self.journal)
            self.assertEqual(content, 'payload')
            return expected_moves
        with patch.object(
                type(self.env['account.move.import_file']),
                '_import_file_none',
                autospec=True,
                side_effect=_fake_import):
            result = wizard._import_file()
        self.assertEqual(result.ids, expected_moves.ids)

    def test_import_file_returns_action_for_imported_moves(self):
        wizard = self._new_wizard()
        imported_moves = self.move_1 | self.move_2
        with patch.object(
                type(self.env['account.move.import_file']),
                '_import_file',
                autospec=True,
                return_value=imported_moves):
            action = wizard.import_file()
        self.assertEqual(action['domain'], [('id', 'in', imported_moves.ids)])
