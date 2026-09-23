###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import base64

from odoo.tests.common import TransactionCase
from odoo.tools import file_open


class TestAccountMoveImportComeralia(TransactionCase):

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
            'type': 'sale',
            'default_credit_account_id': account_642.id,
            'default_debit_account_id': account_642.id,
            'refund_sequence': True,
        })
        wizard_obj = self.env['account.move.import_file'].with_context({
            'active_model': 'account.journal',
            'active_ids': [journal.id],
        })
        content = file_open(
            'account_move_import_comeralia/tests/files/example.dat'
            , 'rb').read()
        wizard = wizard_obj.create({
            'file': base64.b64encode(content),
            'filename': 'example.dat',
            'type': 'payroll_comeralia',
        })
        user_1 = self.env['res.users'].create({
            'login': 'employee_1',
            'name': 'Employee 1',
            'company_id': self.env.ref('base.main_company').id,
        })
        self.env['hr.employee'].create({
            'name': 'Test employee 1',
            'user_id': user_1.id,
            'comeralia_name': 'TEST EMPLOYEE 1',
        })
        user_2 = self.env['res.users'].create({
            'login': 'employee_2',
            'name': 'Employee 2',
            'company_id': self.env.ref('base.main_company').id,
        })
        self.env['hr.employee'].create({
            'name': 'Test employee 2',
            'user_id': user_2.id,
            'comeralia_name': 'TEST EMPLOYEE 2',
        })
        moves = wizard._import_file()
        self.assertEquals(len(moves), 3)
        self.assertEquals(len(moves[0].line_ids), 4)
        move_line_640 = moves[0].line_ids.filtered(
            lambda ln: '640' in ln.account_id.code)
        self.assertEquals(move_line_640.partner_id, user_1.partner_id)
        self.assertEquals(move_line_640.account_id, account_640)
        self.assertEquals(move_line_640.debit, 7238.80)
        self.assertEquals(len(move_line_640.tax_ids), 1)
        self.assertFalse(move_line_640.tax_line_id)
        move_line_465 = moves[0].line_ids.filtered(
            lambda ln: '465' in ln.account_id.code)
        self.assertEquals(move_line_465.partner_id, user_1.partner_id)
        self.assertEquals(move_line_465.account_id, account_465)
        self.assertEquals(move_line_465.credit, 3806.81)
        self.assertEquals(len(move_line_465.tax_ids), 0)
        self.assertFalse(move_line_465.tax_line_id)
        move_line_476 = moves[0].line_ids.filtered(
            lambda ln: '476' in ln.account_id.code)
        self.assertEquals(move_line_476.partner_id, user_1.partner_id)
        self.assertEquals(move_line_476.account_id, account_476)
        self.assertEquals(move_line_476.credit, 1477.51)
        self.assertEquals(len(move_line_476.tax_ids), 0)
        self.assertFalse(move_line_476.tax_line_id)
        move_line_4751 = moves[0].line_ids.filtered(
            lambda ln: '4751' in ln.account_id.code)
        self.assertEquals(move_line_4751.partner_id, user_1.partner_id)
        self.assertEquals(move_line_4751.account_id, account_4751)
        self.assertEquals(move_line_4751.credit, 1954.48)
        self.assertEquals(len(move_line_4751.tax_ids), 0)
        self.assertEquals(irpf_tax, move_line_4751.tax_line_id)
        move_line_640 = moves[1].line_ids.filtered(
            lambda ln: '640' in ln.account_id.code)
        self.assertEquals(move_line_640.partner_id, user_2.partner_id)
        self.assertEquals(move_line_640.account_id, account_640)
        self.assertEquals(move_line_640.debit, 3704.71)
        self.assertEquals(len(move_line_640.tax_ids), 1)
        self.assertFalse(move_line_640.tax_line_id)
        move_line_465 = moves[1].line_ids.filtered(
            lambda ln: '465' in ln.account_id.code)
        self.assertEquals(move_line_465.partner_id, user_2.partner_id)
        self.assertEquals(move_line_465.account_id, account_465)
        self.assertEquals(move_line_465.credit, 2749.02)
        self.assertEquals(len(move_line_465.tax_ids), 0)
        self.assertFalse(move_line_465.tax_line_id)
        move_lines_476 = moves[1].line_ids.filtered(
            lambda ln: '476' in ln.account_id.code)
        self.assertEquals(len(move_lines_476), 2)
        move_line_476 = move_lines_476[0]
        self.assertEquals(move_line_476.partner_id, user_2.partner_id)
        self.assertEquals(move_line_476.account_id, account_476)
        self.assertEquals(move_line_476.credit, 8.64)
        self.assertEquals(len(move_line_476.tax_ids), 0)
        self.assertFalse(move_line_476.tax_line_id)
        move_line_476 = move_lines_476[1]
        self.assertEquals(move_line_476.partner_id, user_2.partner_id)
        self.assertEquals(move_line_476.account_id, account_476)
        self.assertEquals(move_line_476.credit, 280.20)
        self.assertEquals(len(move_line_476.tax_ids), 0)
        self.assertFalse(move_line_476.tax_line_id)
        move_line_4751 = moves[1].line_ids.filtered(
            lambda ln: '4751' in ln.account_id.code)
        self.assertEquals(
            move_line_4751.partner_id, user_2.partner_id)
        self.assertEquals(move_line_4751.account_id, account_4751)
        self.assertEquals(move_line_4751.credit, 666.85)
        self.assertEquals(len(move_line_4751.tax_ids), 0)
        self.assertEquals(irpf_tax, move_line_4751.tax_line_id)
        company_move = moves.filtered(
            lambda m: m.partner_id == self.env.user.company_id.partner_id)
        self.assertEquals(len(company_move), 1)

    def test_access_account_mapped_and_iprf(self):
        account_640 = self.env.ref('l10n_es.1_account_common_640')
        account_640_2 = account_640.copy({'code': '640002'})
        account_465 = self.env.ref('l10n_es.1_account_common_465')
        account_642 = self.env.ref('l10n_es.1_account_common_642')
        account_476 = self.env.ref('l10n_es.1_account_common_476')
        account_4751 = self.env.ref('l10n_es.1_account_common_4751')
        irpf_tax = self.env.ref('l10n_es.1_account_tax_template_p_irpf21t')
        journal = self.env['account.journal'].create({
            'name': 'Test import',
            'code': 'TINV',
            'type': 'sale',
            'default_credit_account_id': account_642.id,
            'default_debit_account_id': account_642.id,
            'refund_sequence': True,
        })
        wizard_obj = self.env['account.move.import_file'].with_context({
            'active_model': 'account.journal',
            'active_ids': [journal.id],
        })
        content = file_open(
            'account_move_import_comeralia/tests/files/example_irpf.dat'
            , 'rb').read()
        wizard = wizard_obj.create({
            'file': base64.b64encode(content),
            'filename': 'example.dat',
            'type': 'payroll_comeralia',
        })
        user_1 = self.env['res.users'].create({
            'login': 'employee_1',
            'name': 'Employee 1',
            'company_id': self.env.ref('base.main_company').id,
        })
        self.env['hr.employee'].create({
            'name': 'Test employee 1',
            'user_id': user_1.id,
            'comeralia_name': 'TEST EMPLOYEE 1',
            'comeralia_account_id': account_640_2.id,
        })
        moves = wizard._import_file()
        self.assertEquals(len(moves), 2)
        self.assertEquals(len(moves[0].line_ids), 6)
        move_line_640 = moves[0].line_ids.filtered(
            lambda ln: '640' in ln.account_id.code)
        self.assertEquals(move_line_640.partner_id, user_1.partner_id)
        self.assertEquals(move_line_640.account_id, account_640_2)
        self.assertEquals(move_line_640.debit, 421.74)
        self.assertEquals(len(move_line_640.tax_ids), 1)
        self.assertFalse(move_line_640.tax_line_id)
        move_line_465 = moves[0].line_ids.filtered(
            lambda ln: '465' in ln.account_id.code)
        self.assertEquals(move_line_465.partner_id, user_1.partner_id)
        self.assertEquals(move_line_465.account_id, account_465)
        self.assertEquals(move_line_465.credit, 2539.24)
        self.assertEquals(len(move_line_465.tax_ids), 0)
        self.assertFalse(move_line_465.tax_line_id)
        move_lines_476 = moves[0].line_ids.filtered(
            lambda ln: '476' in ln.account_id.code)
        self.assertEquals(len(move_lines_476), 3)
        move_line_476 = move_lines_476[2]
        self.assertEquals(move_line_476.partner_id, user_1.partner_id)
        self.assertEquals(move_line_476.account_id, account_476)
        self.assertEquals(move_line_476.debit, 3000.3)
        self.assertEquals(len(move_line_476.tax_ids), 1)
        self.assertFalse(move_line_476.tax_line_id)
        move_line_476 = move_lines_476[1]
        self.assertEquals(move_line_476.partner_id, user_1.partner_id)
        self.assertEquals(move_line_476.account_id, account_476)
        self.assertEquals(move_line_476.credit, 258.83)
        self.assertEquals(len(move_line_476.tax_ids), 0)
        self.assertFalse(move_line_476.tax_line_id)
        move_line_476 = move_lines_476[0]
        self.assertEquals(move_line_476.partner_id, user_1.partner_id)
        self.assertEquals(move_line_476.account_id, account_476)
        self.assertEquals(move_line_476.credit, 8)
        self.assertEquals(len(move_line_476.tax_ids), 0)
        self.assertFalse(move_line_476.tax_line_id)
        move_line_4751 = moves[0].line_ids.filtered(
            lambda ln: '4751' in ln.account_id.code)
        self.assertEquals(move_line_4751.partner_id, user_1.partner_id)
        self.assertEquals(move_line_4751.account_id, account_4751)
        self.assertEquals(move_line_4751.credit, 615.97)
        self.assertEquals(len(move_line_4751.tax_ids), 0)
        self.assertEquals(irpf_tax, move_line_4751.tax_line_id)
        company_move = moves.filtered(
            lambda m: m.partner_id == self.env.user.company_id.partner_id)
        self.assertEquals(len(company_move), 1)

    def test_access_account_mapped_and_advance(self):
        account_640 = self.env.ref('l10n_es.1_account_common_640')
        account_465 = self.env.ref('l10n_es.1_account_common_465')
        account_460 = self.env.ref('l10n_es.1_account_common_460')
        account_642 = self.env.ref('l10n_es.1_account_common_642')
        account_476 = self.env.ref('l10n_es.1_account_common_476')
        journal = self.env['account.journal'].create({
            'name': 'Test import',
            'code': 'TINV',
            'type': 'sale',
            'default_credit_account_id': account_642.id,
            'default_debit_account_id': account_642.id,
            'refund_sequence': True,
        })
        wizard_obj = self.env['account.move.import_file'].with_context({
            'active_model': 'account.journal',
            'active_ids': [journal.id],
        })
        content = file_open(
            'account_move_import_comeralia/tests/files/example_advance.dat'
            , 'rb').read()
        wizard = wizard_obj.create({
            'file': base64.b64encode(content),
            'filename': 'example.dat',
            'type': 'payroll_comeralia',
        })
        user_1 = self.env['res.users'].create({
            'login': 'employee_1',
            'name': 'Employee 1',
            'company_id': self.env.ref('base.main_company').id,
        })
        self.env['hr.employee'].create({
            'name': 'Test employee 1',
            'user_id': user_1.id,
            'comeralia_name': 'TEST EMPLOYEE 1',
            'comeralia_account_id': account_640.id,
            'comeralia_account_advance_id': account_460.id,
        })
        moves = wizard._import_file()
        self.assertEquals(len(moves), 2)
        self.assertEquals(len(moves[0].line_ids), 3)
        move_line_460 = moves[0].line_ids.filtered(
            lambda ln: '460' in ln.account_id.code)
        self.assertEquals(move_line_460.partner_id, user_1.partner_id)
        self.assertEquals(move_line_460.account_id, account_460)
        self.assertEquals(move_line_460.debit, 46.81)
        self.assertEquals(len(move_line_460.tax_ids), 1)
        self.assertFalse(move_line_460.tax_line_id)
        move_line_465 = moves[0].line_ids.filtered(
            lambda ln: '465' in ln.account_id.code)
        self.assertEquals(move_line_465.partner_id, user_1.partner_id)
        self.assertEquals(move_line_465.account_id, account_465)
        self.assertEquals(move_line_465.credit, 40)
        self.assertEquals(len(move_line_465.tax_ids), 0)
        self.assertFalse(move_line_465.tax_line_id)
        move_line_476 = moves[0].line_ids.filtered(
            lambda ln: '476' in ln.account_id.code)
        self.assertEquals(move_line_476.partner_id, user_1.partner_id)
        self.assertEquals(move_line_476.account_id, account_476)
        self.assertEquals(move_line_476.credit, 6.81)
        self.assertEquals(len(move_line_476.tax_ids), 0)
        self.assertFalse(move_line_476.tax_line_id)
        company_move = moves.filtered(
            lambda m: m.partner_id == self.env.user.company_id.partner_id)
        self.assertEquals(len(company_move), 1)

    def test_task_project_analytic_account(self):
        account_642 = self.env.ref('l10n_es.1_account_common_642')
        account_640 = self.env.ref('l10n_es.1_account_common_640')
        journal = self.env['account.journal'].create({
            'name': 'Test import',
            'code': 'TINV',
            'type': 'sale',
            'default_credit_account_id': account_642.id,
            'default_debit_account_id': account_642.id,
            'refund_sequence': True,
        })
        analytic = self.env['account.analytic.account'].create({
            'name': 'AA Proyecto Nómina',
        })
        project = self.env['project.project'].create({
            'name': 'Proyecto Nómina',
            'analytic_account_id': analytic.id,
        })
        task = self.env['project.task'].create({
            'name': 'Tarea Nómina',
            'project_id': project.id,
        })
        wizard_obj = self.env['account.move.import_file'].with_context({
            'active_model': 'account.journal',
            'active_ids': [journal.id],
        })
        content = file_open(
            'account_move_import_comeralia/tests/files/example.dat', 'rb').read()
        wizard = wizard_obj.create({
            'file': base64.b64encode(content),
            'filename': 'example.dat',
            'type': 'payroll_comeralia',
        })
        user_1 = self.env['res.users'].create({
            'login': 'employee_1_task',
            'name': 'Employee 1',
            'company_id': self.env.ref('base.main_company').id,
        })
        self.env['hr.employee'].create({
            'name': 'Test employee 1',
            'user_id': user_1.id,
            'comeralia_name': 'TEST EMPLOYEE 1',
            'comeralia_project_task_id': task.id,
        })
        user_2 = self.env['res.users'].create({
            'login': 'employee_2_notask',
            'name': 'Employee 2',
            'company_id': self.env.ref('base.main_company').id,
        })
        self.env['hr.employee'].create({
            'name': 'Test employee 2',
            'user_id': user_2.id,
            'comeralia_name': 'TEST EMPLOYEE 2',
        })
        moves = wizard._import_file()
        move_emp1 = moves.filtered(lambda m: m.partner_id == user_1.partner_id)
        self.assertTrue(move_emp1)
        for line in move_emp1.line_ids:
            if line.account_id == account_640:
                self.assertEqual(line.analytic_account_id, analytic)
            else:
                self.assertEqual(line.analytic_account_id.id, False)
        move_emp2 = moves.filtered(lambda m: m.partner_id == user_2.partner_id)
        self.assertTrue(move_emp2)
        for line in move_emp2.line_ids:
            self.assertFalse(line.analytic_account_id)
