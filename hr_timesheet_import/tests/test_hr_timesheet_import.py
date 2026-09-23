###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import json
from datetime import datetime

from odoo import exceptions, fields
from odoo.tests.common import HttpCase


class TestHrTimesheetImport(HttpCase):

    def setUp(self):
        super().setUp()
        self.user = self.env['res.users'].create({
            'name': 'New user test',
            'login': 'newtest',
            'email': 'newuser@test.com',
        })
        self.data_test = {
            'enrollment': 12,
            'date': fields.Date.today().strftime('%Y-%m-%d'),
            'incomplete': 'f',
            'signedhoursamount': 8.83,
        }
        self.employee = self.env['hr.employee'].create({
            'name': 'Test employee',
            'company_id': self.env.company.id,
            'user_id': self.user.id,
        })

    def get_minutes(self, float_value):
        minutes = float_value - int(float_value)
        return int(minutes * 60)

    def test_url_import_timesheet_controller_01(self):
        self.employee.signing_identifier = '12'
        self.assertEqual(self.employee.signing_identifier, '12')
        self.authenticate('admin', 'admin')
        self.opener.headers.update({
            'Content-type': 'application/json',
            'Accept': 'text/plain',
        })
        response = self.url_open(
            '/hr_timesheet/import', data=json.dumps(self.data_test))
        self.assertEqual(response.status_code, 200)

    def test_import_timesheet_controller_01(self):
        self.employee.signing_identifier = '12'
        self.assertEqual(self.employee.signing_identifier, '12')
        res = self.env['hr_timesheet.sheet'].import_timesheet(self.data_test)
        sheet = self.env['hr_timesheet.sheet'].search([
            ('id', '=', res),
        ])
        self.assertEqual(len(sheet), 1)
        self.assertEqual(
            sheet.imported_hours, self.data_test['signedhoursamount'])
        self.assertEqual(sheet.employee_id, self.employee)
        date_object = datetime.strptime(
            self.data_test['date'], "%Y-%m-%d").date()
        self.assertEqual(date_object, sheet.date_start)
        self.assertEqual(date_object, sheet.date_end)
        self.assertEqual(sheet.state, 'draft')
        self.assertEqual(sheet.review_policy, 'hr')

    def test_import_timesheet_controller_02(self):
        project = self.env['project.project'].create({
            'name': 'Test project',
            'company_id': self.user.company_id.id,
            'allow_timesheets': True,
            'user_id': self.user.id,
        })
        self.employee.signing_identifier = '12'
        self.assertEqual(self.employee.signing_identifier, '12')
        res = self.env['hr_timesheet.sheet'].import_timesheet(self.data_test)
        sheet = self.env['hr_timesheet.sheet'].search([
            ('id', '=', res),
        ])
        self.assertEqual(len(sheet), 1)
        self.assertEqual(len(sheet.timesheet_ids), 0)
        timesheet_data_01 = {
            'name': 'Time task test 1',
            'project_id': project.id,
            'employee_id': self.employee.id,
            'sheet_id': sheet.id,
            'unit_amount': 4.5,
            'date': fields.Date.today().strftime('%Y-%m-%d'),
        }
        timesheet_line = self.env['account.analytic.line'].create(
            timesheet_data_01)
        sheet.timesheet_ids = timesheet_line
        sheet._onchange_timesheets()
        self.assertEqual(len(sheet.timesheet_ids), 1)
        self.assertEqual(len(sheet.line_ids), 1)
        self.assertEqual(timesheet_line.unit_amount, 4.5)
        self.assertEqual(sheet.timesheet_ids.unit_amount, 4.5)
        self.assertEqual(self.get_minutes(sheet.remaining_hours), 19)
        self.assertTrue(sheet.remaining_hours > 0)
        timesheet_data_02 = {
            'name': 'Time task test 2',
            'project_id': project.id,
            'employee_id': self.employee.id,
            'sheet_id': sheet.id,
            'unit_amount': 4.33,
            'date': fields.Date.today().strftime('%Y-%m-%d'),
        }
        timesheet_line_02 = self.env['account.analytic.line'].create(
            timesheet_data_02)
        sheet._onchange_timesheets()
        self.assertEqual(len(sheet.timesheet_ids), 2)
        self.assertEqual(timesheet_line_02.unit_amount, 4.33)
        self.assertEqual(sum(sheet.timesheet_ids.mapped('unit_amount')), 8.83)
        self.assertEqual(
            sum(sheet.timesheet_ids.mapped('unit_amount')),
            sheet.imported_hours)
        timesheet_data_03 = {
            'name': 'Time task test 3',
            'project_id': project.id,
            'employee_id': self.employee.id,
            'sheet_id': sheet.id,
            'unit_amount': 2,
            'date': fields.Date.today().strftime('%Y-%m-%d'),
        }
        timesheet_line_03 = self.env['account.analytic.line'].create(
            timesheet_data_03)
        sheet._onchange_timesheets()
        self.assertEqual(len(sheet.timesheet_ids), 3)
        self.assertEqual(timesheet_line_03.unit_amount, 2)
        self.assertEqual(sum(sheet.timesheet_ids.mapped('unit_amount')), 10.83)
        self.assertTrue(sheet.remaining_hours < 0)

    def test_check_vals_keys_controller_import(self):
        self.employee.signing_identifier = '12'
        self.assertEqual(self.employee.signing_identifier, '12')
        del self.data_test['enrollment']
        with self.assertRaises(exceptions.ValidationError) as result:
            self.env['hr_timesheet.sheet'].import_timesheet(self.data_test)
        self.assertEqual('Missing data for import', result.exception.args[0])

    def test_incomplete_timesheet_import(self):
        self.employee.signing_identifier = '12'
        self.assertEqual(self.employee.signing_identifier, '12')
        self.data_test.update({
            'signedhoursamount': 0,
            'incomplete': 't',
        })
        res = self.env['hr_timesheet.sheet'].import_timesheet(self.data_test)
        sheet = self.env['hr_timesheet.sheet'].search([
            ('id', '=', res),
        ])
        self.assertEqual(len(sheet), 1)
        self.assertFalse(sheet.sheet_complete)
        self.assertEqual(sheet.imported_hours, 0)
        self.assertEqual(sheet.remaining_hours, 0)

    def test_error_not_found_user_import(self):
        self.employee.signing_identifier = '12'
        self.assertEqual(self.employee.signing_identifier, '12')
        self.data_test['enrollment'] = '15'
        with self.assertRaises(exceptions.ValidationError) as result:
            self.env['hr_timesheet.sheet'].import_timesheet(self.data_test)
        self.assertIn(
            'Employee with identifier 15 not found', result.exception.args[0])

    def test_error_api_constrains_duplicated_identifier(self):
        self.employee.signing_identifier = '12'
        self.assertEqual(self.employee.signing_identifier, '12')
        with self.assertRaises(exceptions.ValidationError) as result:
            employee_test = self.env['hr.employee'].create({
                'name': 'Test employee v2',
                'company_id': self.env.company.id,
            })
            employee_test.signing_identifier = '12'
        self.assertIn('The identifier for signing', result.exception.args[0])
        self.assertIn('already exists', result.exception.args[0])

    def test_update_timesheet_controller(self):
        self.employee.signing_identifier = '12'
        self.assertEqual(self.employee.signing_identifier, '12')
        self.data_test.update({
            'signedhoursamount': 0,
            'incomplete': 't',
        })
        res_01 = self.env['hr_timesheet.sheet'].import_timesheet(
            self.data_test)
        sheet_01 = self.env['hr_timesheet.sheet'].search([
            ('id', '=', res_01),
        ])
        self.assertEqual(len(sheet_01), 1)
        self.assertFalse(sheet_01.sheet_complete)
        self.assertEqual(sheet_01.imported_hours, 0)
        self.assertEqual(sheet_01.remaining_hours, 0)
        messages_01 = sheet_01.message_ids
        self.assertIn(
            'Timesheet imported through the controller on date',
            sheet_01.message_ids[0].body)
        self.data_test.update({
            'incomplete': 'f',
            'signedhoursamount': 6.37,
        })
        res_02 = self.env['hr_timesheet.sheet'].import_timesheet(
            self.data_test)
        sheet_02 = self.env['hr_timesheet.sheet'].search([
            ('id', '=', res_02),
        ])
        self.assertEqual(len(sheet_02), 1)
        self.assertEqual(sheet_01, sheet_02)
        self.assertTrue(sheet_02.sheet_complete)
        self.assertEqual(sheet_02.imported_hours, 6.37)
        messages_02 = sheet_02.message_ids
        self.assertNotEqual(len(messages_02), len(messages_01))
        self.assertEqual(len(messages_02), len(messages_01) + 1)
        self.assertIn(
            'Timesheet updated through the controller on date',
            sheet_02.message_ids[0].body)

    def test_remaining_hours_round(self):
        project = self.env['project.project'].create({
            'name': 'Test project',
            'company_id': self.user.company_id.id,
            'allow_timesheets': True,
            'user_id': self.user.id,
        })
        self.employee.signing_identifier = '12'
        self.assertEqual(self.employee.signing_identifier, '12')
        data = {
            'enrollment': 12,
            'date': fields.Date.today().strftime('%Y-%m-%d'),
            'incomplete': 'f',
            'signedhoursamount': 8.516666667,
        }
        res = self.env['hr_timesheet.sheet'].import_timesheet(data)
        sheet = self.env['hr_timesheet.sheet'].search([
            ('id', '=', res),
        ])
        self.assertEqual(len(sheet), 1)
        self.assertEqual(len(sheet.timesheet_ids), 0)
        timesheet_data_01 = {
            'name': 'Time task test 1',
            'project_id': project.id,
            'employee_id': self.employee.id,
            'sheet_id': sheet.id,
            'unit_amount': 8.516666667,
            'date': fields.Date.today().strftime('%Y-%m-%d'),
        }
        timesheet_line = self.env['account.analytic.line'].create(
            timesheet_data_01)
        sheet.timesheet_ids = timesheet_line
        sheet._onchange_timesheets()
        self.assertEqual(len(sheet.timesheet_ids), 1)
        self.assertEqual(len(sheet.line_ids), 1)
        self.assertEqual(timesheet_line.unit_amount, 8.516666667)
        self.assertEqual(sheet.timesheet_ids.unit_amount, 8.516666667)
        self.assertEqual(sheet.remaining_hours, 0)
        self.assertEqual(sheet.imported_hours, 8.516666667)
        self.assertTrue(sheet.sheet_complete)

    def test_remaining_hours_round_two_lines(self):
        project = self.env['project.project'].create({
            'name': 'Test project',
            'company_id': self.user.company_id.id,
            'allow_timesheets': True,
            'user_id': self.user.id,
        })
        self.employee.signing_identifier = '12'
        self.assertEqual(self.employee.signing_identifier, '12')
        data = {
            'enrollment': 12,
            'date': fields.Date.today().strftime('%Y-%m-%d'),
            'incomplete': 'f',
            'signedhoursamount': 8.17,
        }
        res = self.env['hr_timesheet.sheet'].import_timesheet(data)
        sheet = self.env['hr_timesheet.sheet'].search([
            ('id', '=', res),
        ])
        self.assertEqual(len(sheet), 1)
        self.assertEqual(len(sheet.timesheet_ids), 0)
        timesheet_line_1 = self.env['account.analytic.line'].create({
            'name': 'Time task test 1',
            'project_id': project.id,
            'employee_id': self.employee.id,
            'sheet_id': sheet.id,
            'unit_amount': 8,
            'date': fields.Date.today().strftime('%Y-%m-%d'),
        })
        sheet.timesheet_ids = timesheet_line_1
        sheet._onchange_timesheets()
        self.assertEqual(len(sheet.timesheet_ids), 1)
        self.assertEqual(len(sheet.line_ids), 1)
        self.assertEqual(timesheet_line_1.unit_amount, 8.0)
        self.assertEqual(sheet.timesheet_ids.unit_amount, 8.0)
        self.assertEqual(self.get_minutes(sheet.remaining_hours), 10)
        self.assertEqual(sheet.imported_hours, 8.17)
        self.assertTrue(sheet.sheet_complete)
        timesheet_line_2 = self.env['account.analytic.line'].create({
            'name': 'Time task test 2',
            'project_id': project.id,
            'employee_id': self.employee.id,
            'sheet_id': sheet.id,
            'unit_amount': .17,
            'date': fields.Date.today().strftime('%Y-%m-%d'),
        })
        sheet.timesheet_ids |= timesheet_line_2
        sheet._onchange_timesheets()
        self.assertEqual(len(sheet.timesheet_ids), 2)
        self.assertEqual(len(sheet.line_ids), 1)
        self.assertEqual(timesheet_line_2.unit_amount, .17)
        self.assertEqual(sheet.remaining_hours, 0.0)
        self.assertEqual(sheet.imported_hours, 8.17)
        self.assertTrue(sheet.sheet_complete)
