###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from datetime import date

from odoo.tests import TransactionCase


class TestHrEmployeeStates(TransactionCase):

    def setUp(self):
        super().setUp()
        self.employee = self.env['hr.employee'].create({
            'name': 'Test Employee',
        })
        self.test_user = self.env['res.users'].create({
            'name': 'Employee',
            'login': 'internal',
            'groups_id': [(4, self.env.ref('base.group_user').id)],
        })

    def test_create_employee(self):
        self.assertEqual(self.employee.state, 'applicant')
        state_history = self.env['hr.employee.state.history'].search([
            ('employee_id', '=', self.employee.id),
        ])
        self.assertTrue(state_history)
        self.assertEqual(state_history.start_date, date.today())
        self.assertEqual(state_history.state, 'applicant')

    def test_set_as_applicant(self):
        self.employee.set_as_applicant()
        self.assertEqual(self.employee.state, 'applicant')
        state_history = self.env['hr.employee.state.history'].search([
            ('employee_id', '=', self.employee.id),
            ('state', '=', 'applicant'),
            ('start_date', '=', date.today()),
            ('end_date', '=', False),
        ])
        self.assertTrue(state_history)

    def test_set_as_employee(self):
        self.test_set_as_applicant()
        self.employee.set_as_employee()
        self.assertEqual(self.employee.state, 'employment')
        state_history = self.env['hr.employee.state.history'].search([
            ('employee_id', '=', self.employee.id),
            ('state', '=', 'applicant'),
            ('end_date', '!=', False),
        ])
        self.assertTrue(state_history)
        state_history = self.env['hr.employee.state.history'].search([
            ('employee_id', '=', self.employee.id),
            ('state', '=', 'employment'),
            ('start_date', '=', date.today()),
            ('end_date', '=', False),
        ])
        self.assertTrue(state_history)

    def test_set_as_discarded(self):
        self.test_set_as_employee()
        self.employee.set_as_discarded()
        self.assertEqual(self.employee.state, 'discarded')
        state_history = self.env['hr.employee.state.history'].search([
            ('employee_id', '=', self.employee.id),
            ('state', '=', 'employment'),
            ('end_date', '!=', False),
        ])
        self.assertTrue(state_history)
        state_history = self.env['hr.employee.state.history'].search([
            ('employee_id', '=', self.employee.id),
            ('state', '=', 'discarded'),
            ('start_date', '=', date.today()),
            ('end_date', '=', False),
        ])
        self.assertTrue(state_history)

    def test_set_as_inactive(self):
        self.test_set_as_applicant()
        self.employee.set_as_inactive()
        self.assertEqual(self.employee.state, 'inactive')
        state_history = self.env['hr.employee.state.history'].search([
            ('employee_id', '=', self.employee.id),
            ('state', '=', 'discarded'),
            ('end_date', '!=', False),
        ])
        self.assertFalse(state_history)
        state_history = self.env['hr.employee.state.history'].search([
            ('employee_id', '=', self.employee.id),
            ('state', '=', 'inactive'),
            ('start_date', '=', date.today()),
            ('end_date', '=', False),
        ])
        self.assertTrue(state_history)

    def test_wizard_set_user_employee(self):
        wizard = self.env['wizard.set.employee'].with_context(
            employee_id=self.employee.id).create({
                'related_user': self.test_user.id,
            })
        wizard.set_employee()
        self.assertEqual(self.employee.user_id, self.test_user)
        self.assertEqual(self.employee.state, 'employment')
        state_history = self.env['hr.employee.state.history'].search([
            ('employee_id', '=', self.employee.id),
            ('state', '=', 'employment'),
        ])
        self.assertTrue(state_history)
