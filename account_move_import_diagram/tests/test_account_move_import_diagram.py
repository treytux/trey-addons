###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import base64

from odoo import exceptions
from odoo.tests.common import TransactionCase
from odoo.tools import file_open


class TestAccountMoveImportDiagram(TransactionCase):

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
        account_471 = self.env.ref('l10n_es.1_account_common_471')
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
            'account_move_import_diagram/tests/files/sample.xls', 'rb').read()
        wizard = wizard_obj.create({
            'file': base64.b64encode(content),
            'filename': 'sample.xls',
            'type': 'diagram',
        })
        with self.assertRaises(exceptions.ValidationError):
            wizard.import_file()
        employee_1 = self.env['hr.employee'].create({
            'name': 'EMPLEADO 1',
            'identification_id': '12345678Z',
        })
        with self.assertRaises(exceptions.ValidationError):
            wizard.import_file()
        employee_1.user_id = self.env.user.id
        self.assertEqual(
            employee_1.user_id.partner_id, self.env.user.partner_id)
        user_2 = self.env.user.create({
            'name': 'EMPLEADO 2',
            'login': 'empleado2@trey.es',
        })
        employee_2 = self.env['hr.employee'].create({
            'name': 'OTHER EMPLOYEE',
            'identification_id': '2A',
            'user_id': user_2.id,
        })
        user_3 = self.env.user.create({
            'name': 'EMPLEADO 3',
            'login': 'empleado3@trey.es',
        })
        employee_3 = self.env['hr.employee'].create({
            'name': 'OTHER EMPLOYEE 3',
            'identification_id': '3A',
            'user_id': user_3.id,
        })
        wizard.import_file()
        moves = self.env['account.move'].search(
            [('journal_id', '=', journal.id)])
        self.assertEqual(len(moves), 3)
        move = moves.filtered(
            lambda m: m.partner_id == employee_1.user_id.partner_id)
        self.assertEqual(len(move.line_ids), 6)
        self.assertEqual(
            move.line_ids[0].partner_id, employee_1.user_id.partner_id)
        move_line_465 = move.line_ids.filtered(
            lambda ln: '465' in ln.account_id.code)
        self.assertEqual(
            move_line_465.partner_id, employee_1.user_id.partner_id)
        self.assertEqual(move_line_465.account_id, account_465)
        self.assertEqual(move_line_465.credit, 1301.41)
        move_line_640 = move.line_ids.filtered(
            lambda ln: '640' in ln.account_id.code)
        self.assertEqual(
            move_line_640.partner_id, employee_1.user_id.partner_id)
        self.assertEqual(move_line_640.account_id, account_640)
        self.assertEqual(move_line_640.debit, 1452.15)
        self.assertEqual(len(move_line_640.tax_ids), 1)
        self.assertFalse(move_line_640.tax_line_id)
        move_line_4751 = move.line_ids.filtered(
            lambda ln: '4751' in ln.account_id.code)
        self.assertEqual(
            move_line_4751.partner_id, employee_1.user_id.partner_id)
        self.assertEqual(move_line_4751.account_id, account_4751)
        self.assertEqual(move_line_4751.credit, 43.85)
        self.assertEqual(len(move_line_4751.tax_ids), 0)
        self.assertEqual(irpf_tax, move_line_4751.tax_line_id)
        move_line_642 = move.line_ids.filtered(
            lambda ln: '642' in ln.account_id.code)
        self.assertEqual(
            move_line_642.partner_id, employee_1.user_id.partner_id)
        self.assertEqual(move_line_642.account_id, account_642)
        self.assertEqual(round(move_line_642.debit, 2), 182.39)
        move_line_476 = move.line_ids.filtered(
            lambda ln: '476' in ln.account_id.code)
        self.assertEqual(
            move_line_476.partner_id, employee_1.user_id.partner_id)
        self.assertEqual(move_line_476.account_id, account_476)
        self.assertEqual(round(sum(move_line_476.mapped('credit')), 2), 289.28)
        self.assertEqual(move.partner_id, employee_1.user_id.partner_id)
        self.assertEqual(move.partner_id, employee_1.user_id.partner_id)
        move = moves.filtered(
            lambda m: m.partner_id == employee_2.user_id.partner_id)
        self.assertEqual(len(move.line_ids), 6)
        self.assertEqual(
            move.line_ids[0].partner_id, employee_2.user_id.partner_id)
        move_line_465 = move.line_ids.filtered(
            lambda ln: '465' in ln.account_id.code)
        self.assertEqual(
            move_line_465.partner_id, employee_2.user_id.partner_id)
        self.assertEqual(move_line_465.account_id, account_465)
        self.assertEqual(move_line_465.credit, 2434.00)
        move_line_640 = move.line_ids.filtered(
            lambda ln: '640' in ln.account_id.code)
        self.assertEqual(
            move_line_640.partner_id, employee_2.user_id.partner_id)
        self.assertEqual(move_line_640.account_id, account_640)
        self.assertEqual(move_line_640.debit, 3615.79)
        self.assertEqual(len(move_line_640.tax_ids), 1)
        self.assertFalse(move_line_640.tax_line_id)
        move_line_4751 = move.line_ids.filtered(
            lambda ln: '4751' in ln.account_id.code)
        self.assertEqual(
            move_line_4751.partner_id, employee_2.user_id.partner_id)
        self.assertEqual(move_line_4751.account_id, account_4751)
        self.assertEqual(move_line_4751.credit, 867.79)
        self.assertEqual(len(move_line_4751.tax_ids), 0)
        self.assertEqual(irpf_tax, move_line_4751.tax_line_id)
        move_line_642 = move.line_ids.filtered(
            lambda ln: '642' in ln.account_id.code)
        self.assertEqual(
            move_line_642.partner_id, employee_2.user_id.partner_id)
        self.assertEqual(move_line_642.account_id, account_642)
        self.assertEqual(round(move_line_642.debit, 2), 0.0)
        move_line_476 = move.line_ids.filtered(
            lambda ln: '476' in ln.account_id.code)
        self.assertEqual(
            move_line_476.partner_id, employee_2.user_id.partner_id)
        self.assertEqual(move_line_476.account_id, account_476)
        self.assertEqual(round(sum(move_line_476.mapped('credit')), 2), 0.0)
        self.assertEqual(move.partner_id, employee_2.user_id.partner_id)
        move = moves.filtered(
            lambda m: m.partner_id == employee_3.user_id.partner_id)
        self.assertEqual(len(move.line_ids), 7)
        self.assertEqual(
            move.line_ids[0].partner_id, employee_3.user_id.partner_id)
        move_line_465 = move.line_ids.filtered(
            lambda ln: '465' in ln.account_id.code)
        self.assertEqual(
            move_line_465.partner_id, employee_3.user_id.partner_id)
        self.assertEqual(move_line_465.account_id, account_465)
        self.assertEqual(move_line_465.credit, 1238.69)
        move_line_640 = move.line_ids.filtered(
            lambda ln: '640' in ln.account_id.code)
        self.assertEqual(
            move_line_640.partner_id, employee_3.user_id.partner_id)
        self.assertEqual(move_line_640.account_id, account_640)
        self.assertEqual(move_line_640.debit, 79.19)
        self.assertEqual(len(move_line_640.tax_ids), 1)
        self.assertFalse(move_line_640.tax_line_id)
        move_line_4751 = move.line_ids.filtered(
            lambda ln: '4751' in ln.account_id.code)
        self.assertEqual(
            move_line_4751.partner_id, employee_3.user_id.partner_id)
        self.assertEqual(move_line_4751.account_id, account_4751)
        self.assertEqual(move_line_4751.credit, 30.82)
        self.assertEqual(len(move_line_4751.tax_ids), 0)
        self.assertEqual(irpf_tax, move_line_4751.tax_line_id)
        move_line_642 = move.line_ids.filtered(
            lambda ln: '642' in ln.account_id.code)
        self.assertEqual(
            move_line_642.partner_id, employee_3.user_id.partner_id)
        self.assertEqual(move_line_642.account_id, account_642)
        self.assertEqual(round(move_line_642.debit, 2), 639.67)
        move_line_476 = move.line_ids.filtered(
            lambda ln: '476' in ln.account_id.code)
        self.assertEqual(
            move_line_476.partner_id, employee_3.user_id.partner_id)
        self.assertEqual(move_line_476.account_id, account_476)
        self.assertEqual(round(sum(move_line_476.mapped('credit')), 2), 752.25)
        self.assertEqual(move.partner_id, employee_3.user_id.partner_id)
        move_line_471 = move.line_ids.filtered(
            lambda ln: '471' in ln.account_id.code)
        self.assertEqual(
            move_line_471.partner_id, employee_3.user_id.partner_id)
        self.assertEqual(move_line_471.account_id, account_471)
        self.assertEqual(round(sum(move_line_471.mapped('debit')), 2), 1302.90)
        self.assertEqual(move.partner_id, employee_3.user_id.partner_id)
