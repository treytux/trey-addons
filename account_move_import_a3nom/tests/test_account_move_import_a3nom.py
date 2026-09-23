###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import base64

from odoo import exceptions
from odoo.tests.common import TransactionCase
from odoo.tools import file_open


class TestAccountMoveImportA3nom(TransactionCase):

    def setUp(self):
        super().setUp()
        chart_template = self.env.ref('l10n_es.account_chart_template_common')
        chart_template.with_context(
            lang='es_ES',
            install_mode=True,
            company_id=self.env.company
        ).try_loading(company=self.env.company)

    def test_access_account(self):
        account_640 = self.env.ref('l10n_es.1_account_common_640')
        account_465 = self.env.ref('l10n_es.1_account_common_465')
        account_642 = self.env.ref('l10n_es.1_account_common_642')
        account_476 = self.env.ref('l10n_es.1_account_common_476')
        account_4751 = self.env.ref('l10n_es.1_account_common_4751')
        irpf_tax = self.env.ref('l10n_es.1_account_tax_template_p_irpf21t')
        journal = self.env['account.journal'].create({
            'name': 'Test import',
            'code': 'TINV',
            'type': 'general',
            'default_account_id': account_642.id,
            'refund_sequence': True,
        })
        wizard_obj = self.env['account.move.import_file'].with_context({
            'active_model': 'account.journal',
            'active_ids': [journal.id],
        })
        content = file_open(
            'account_move_import_a3nom/tests/files/example.dat', 'rb').read()
        wizard = wizard_obj.create({
            'file': base64.b64encode(content),
            'filename': 'example.dat',
            'type': 'a3nom',
        })
        with self.assertRaises(exceptions.ValidationError):
            wizard.import_file()
        employee = self.env['hr.employee'].create({
            'name': 'Test employee',
            'a3nom_company': 424,
            'a3nom_code': '1',
        })
        with self.assertRaises(exceptions.ValidationError):
            wizard.import_file()
        employee.user_id = self.env.user.id
        self.assertEqual(
            employee.user_id.partner_id, self.env.user.partner_id)
        wizard.import_file()
        moves = self.env['account.move'].search([
            ('journal_id', '=', journal.id),
        ])
        self.assertEqual(len(moves), 1)
        self.assertEqual(len(moves.line_ids), 5)
        move_line_465 = moves.line_ids.filtered(
            lambda ln: '465' in ln.account_id.code)
        self.assertEqual(move_line_465.partner_id, self.env.user.partner_id)
        self.assertEqual(move_line_465.account_id, account_465)
        self.assertEqual(move_line_465.credit, 1252.58)
        move_line_640 = moves.line_ids.filtered(
            lambda ln: '640' in ln.account_id.code)
        self.assertEqual(move_line_640.partner_id, self.env.user.partner_id)
        self.assertEqual(move_line_640.account_id, account_640)
        self.assertEqual(move_line_640.debit, 1409.93)
        self.assertEqual(len(move_line_640.tax_ids), 1)
        self.assertFalse(move_line_640.tax_line_id)
        move_line_4751 = moves.line_ids.filtered(
            lambda ln: '4751' in ln.account_id.code)
        self.assertEqual(move_line_4751.partner_id, self.env.user.partner_id)
        self.assertEqual(move_line_4751.account_id, account_4751)
        self.assertEqual(move_line_4751.credit, 66.13)
        self.assertEqual(len(move_line_4751.tax_ids), 0)
        self.assertEqual(irpf_tax, move_line_4751.tax_line_id)
        move_line_642 = moves.line_ids.filtered(
            lambda ln: '642' in ln.account_id.code)
        self.assertEqual(move_line_642.partner_id, self.env.user.partner_id)
        self.assertEqual(move_line_642.account_id, account_642)
        self.assertEqual(round(move_line_642.debit, 2), 450.9)
        move_line_476 = moves.line_ids.filtered(
            lambda ln: '476' in ln.account_id.code)
        self.assertEqual(move_line_476.partner_id, self.env.user.partner_id)
        self.assertEqual(move_line_476.account_id, account_476)
        self.assertEqual(move_line_476.credit, 542.12)
        self.assertEqual(moves.partner_id, self.env.user.partner_id)
