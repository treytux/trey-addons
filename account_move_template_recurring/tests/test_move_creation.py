###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields
from odoo.tests.common import SavepointCase


class TestMoveCreation(SavepointCase):
    def setUp(self):
        super().setUp()
        self.journal = self.env['account.journal'].create({
            'name': 'Test Journal',
            'code': 'TEST',
            'type': 'general',
        })
        self.account1 = self.env['account.account'].create({
            'name': 'Test Account',
            'code': 'ACCOUNT1',
            'account_type': 'asset_current',
        })
        self.account2 = self.env['account.account'].create({
            'name': 'Test Account',
            'code': 'ACCOUNT2',
            'account_type': 'asset_current',
        })
        self.template = self.env['account.move.template'].create({
            'name': 'Test Entry',
            'journal_id': self.journal.id,
            'line_ids': [
                (0, 0, {
                    'name': 'Test Line',
                    'sequence': 1,
                    'account_id': self.account1.id,
                    'move_line_type': 'cr',
                    'type': 'computed',
                    'python_code': 100.0,
                }),
                (0, 0, {
                    'name': 'Test Line',
                    'sequence': 2,
                    'account_id': self.account2.id,
                    'move_line_type': 'dr',
                    'type': 'computed',
                    'python_code': 100.0,
                }),
            ],
        })

    def test_single_entry(self):
        wiz = self.env['account.move.template.run'].create({
            'template_id': self.template.id,
            'date': fields.Date.today(),
            'ref': 'Test Single Entry',
            'journal_id': self.journal.id,
        })
        wiz.generate_move()
        move_line = self.env['account.move'].search([
            ('ref', '=', 'Test Single Entry'),
        ])
        self.assertEqual(len(move_line), 1)
        self.assertEqual(len(move_line.line_ids), 2)

    def test_multiple_entries(self):
        wiz = self.env['account.move.template.run'].create({
            'template_id': self.template.id,
            'date': fields.Date.today(),
            'ref': 'Test Multiple Entries',
            'journal_id': self.journal.id,
            'times': 10,
        })
        wiz.generate_move()
        move_line = self.env['account.move'].search([
            ('ref', '=', 'Test Multiple Entries'),
        ])
        self.assertEqual(len(move_line), 10)

    def test_multiple_entries_end_month(self):
        wiz = self.env['account.move.template.run'].create({
            'template_id': self.template.id,
            'date': fields.Date.from_string('2023-01-01'),
            'ref': 'Test End Month',
            'journal_id': self.journal.id,
            'times': 2,
            'only_end_month': True,
        })
        wiz.generate_move()
        move_lines = self.env['account.move'].search([
            ('ref', '=', 'Test End Month'),
        ])
        self.assertEqual(
            sorted(move_lines.mapped('date')), [
                fields.Date.from_string('2023-01-31'),
                fields.Date.from_string('2023-02-28'),])

    def test_multiple_entries_quarter(self):
        wiz = self.env['account.move.template.run'].create({
            'template_id': self.template.id,
            'date': fields.Date.from_string('2023-01-15'),
            'ref': 'Test Quarter',
            'journal_id': self.journal.id,
            'times': 3,
            'period': 'quarter',
        })
        wiz.generate_move()
        move_lines = self.env['account.move'].search([
            ('ref', '=', 'Test Quarter'),
        ])
        self.assertEqual(
            sorted(move_lines.mapped('date')), [
                fields.Date.from_string('2023-01-15'),
                fields.Date.from_string('2023-04-15'),
                fields.Date.from_string('2023-07-15')])
