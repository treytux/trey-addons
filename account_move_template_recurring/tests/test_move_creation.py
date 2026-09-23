###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from dateutil.relativedelta import relativedelta
from odoo import fields
from odoo.tests.common import SavepointCase


class TestMoveCreation(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.journal = cls.env['account.journal'].create({
            'name': 'Test Journal',
            'code': 'TEST',
            'type': 'general',
        })
        cls.account1 = cls.env['account.account'].create({
            'name': 'Test Account',
            'code': 'ACCOUNT1',
            'user_type_id':
                cls.env.ref('account.data_account_type_current_assets').id,
        })
        cls.account2 = cls.env['account.account'].create({
            'name': 'Test Account',
            'code': 'ACCOUNT2',
            'user_type_id':
                cls.env.ref('account.data_account_type_current_assets').id,
        })
        cls.template = cls.env['account.move.template'].create({
            'name': 'Test Entry',
            'journal_id': cls.journal.id,
            'line_ids': [
                (0, 0, {
                    'name': 'Test Line',
                    'sequence': 1,
                    'account_id': cls.account1.id,
                    'move_line_type': 'cr',
                    'type': 'computed',
                    'python_code': 100.0,
                }),
                (0, 0, {
                    'name': 'Test Line',
                    'sequence': 2,
                    'account_id': cls.account2.id,
                    'move_line_type': 'dr',
                    'type': 'computed',
                    'python_code': 100.0,
                }),
            ],
        })

    def test_single_entry(self):
        """ Test creation of a single entry """
        wiz = self.env['account.move.template.run'].create({
            'template_id': self.template.id,
            'date': fields.Date.today(),
            'ref': 'Test Single Entry',
            'journal_id': self.journal.id,
        })
        wiz.generate_move()
        move_line = self.env['account.move'].search(
            [('ref', '=', 'Test Single Entry')])
        self.assertEqual(len(move_line), 1)
        self.assertEqual(len(move_line.line_ids), 2)

    def test_multiple_entries(self):
        """ Test creation of multiple entries """
        wiz = self.env['account.move.template.run'].create({
            'template_id': self.template.id,
            'date': fields.Date.today(),
            'ref': 'Test Multiple Entries',
            'journal_id': self.journal.id,
            'times': 10,
        })
        wiz.generate_move()
        move_line = self.env['account.move'].search(
            [('ref', '=', 'Test Multiple Entries')])
        self.assertEqual(len(move_line), 10)

    def test_multiple_entries_end_month(self):
        """ Test is end moth date is correct """
        wiz = self.env['account.move.template.run'].create({
            'template_id': self.template.id,
            'date': '2023-01-01',
            'ref': 'Test End Month',
            'journal_id': self.journal.id,
            'times': 2,
            'only_end_month': True,
        })
        wiz.generate_move()
        move_lines = self.env['account.move'].search(
            [('ref', '=', 'Test End Month')])
        for move in move_lines:
            self.assertEqual(move.date, move.date + relativedelta(day=31))
