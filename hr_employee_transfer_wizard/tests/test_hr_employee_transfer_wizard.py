###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.exceptions import ValidationError
from odoo.tests import TransactionCase


class TestEmployeeTransferWizard(TransactionCase):

    def setUp(self):
        super().setUp()
        self.company_1 = self.env.ref('base.main_company')
        self.employee_user = self.env['res.users'].with_context(
            no_reset_password=True).create({
                'name': 'Test Employee User',
                'login': 'test.employee.user',
                'email': 'test.employee.user@example.com',
                'company_id': self.company_1.id,
                'company_ids': [(6, 0, [self.company_1.id])],
                'groups_id': [(6, 0, [self.env.ref('base.group_user').id])],
            })
        self.employee_address = self.env['res.partner'].create({
            'name': 'Employee Address',
            'email': 'employee.address@example.com',
            'phone': '555000111',
        })
        company_model = self.env['res.company']
        company_values = {
            'name': 'Test Company 2',
        }
        self.company_2 = company_model.create(company_values)
        self.employee_1 = self.env['hr.employee'].create({
            'name': 'Test employee 1',
            'company_id': self.company_1.id,
            'work_email': 'employee1@test.com',
            'work_phone': '123456789',
            'mobile_phone': '987654321',
            'user_id': self.employee_user.id,
            'address_home_id': self.employee_address.id,
        })
        self.employee_2 = self.env['hr.employee'].create({
            'name': 'Test employee 2',
            'company_id': self.company_1.id,
            'work_email': 'employee2@test.com',
        })
        self.wizard = self.env['employee.transfer.wizard'].create({
            'employee_ids': [(6, 0, [self.employee_1.id, self.employee_2.id])],
            'target_company_id': self.company_2.id,
        })

    def test_transfer_employees_basic(self):
        action = self.wizard.action_transfer_employees()
        transferred_ids = action['domain'][0][2]
        transferred_employees = self.env['hr.employee'].search([
            ('id', 'in', transferred_ids),
        ])
        self.assertEqual(len(transferred_employees), 2)
        for emp in transferred_employees:
            self.assertEqual(emp.company_id.id, self.company_2.id)
        original_names = {self.employee_1.name, self.employee_2.name}
        transferred_names = set(transferred_employees.mapped('name'))
        self.assertEqual(original_names, transferred_names)

    def test_transfer_with_additional_fields(self):
        additional_fields = self.env['ir.model.fields'].search([
            ('model_id.model', '=', 'hr.employee'),
            ('name', 'in', ['work_phone', 'mobile_phone']),
        ])
        self.wizard.additional_field_ids = [(6, 0, additional_fields.ids)]
        self.wizard.action_transfer_employees()
        new_employee = self.env['hr.employee'].search([
            ('name', '=', 'Test employee 1'),
            ('company_id', '=', self.company_2.id),
        ])
        self.assertEqual(new_employee.work_phone, '123456789')
        self.assertEqual(new_employee.mobile_phone, '987654321')
        self.assertEqual(new_employee.work_email, 'employee1@test.com')

    def test_transfer_only_base_fields(self):
        self.wizard.action_transfer_employees()
        new_employee = self.env['hr.employee'].search([
            ('name', '=', 'Test employee 1'),
            ('company_id', '=', self.company_2.id),
        ])
        self.assertEqual(new_employee.work_email, 'employee1@test.com')
        self.assertEqual(new_employee.work_phone, '123456789')
        self.assertEqual(new_employee.mobile_phone, '987654321')

    def test_duplicate_name_raises_error(self):
        self.env['hr.employee'].create({
            'name': 'Test employee 1',
            'company_id': self.company_2.id,
        })
        with self.assertRaises(ValidationError):
            self.wizard.action_transfer_employees()

    def test_default_get_with_active_ids(self):
        wizard = self.env['employee.transfer.wizard'].with_context(
            active_ids=[self.employee_1.id]
        ).default_get(['employee_ids'])
        self.assertEqual(wizard['employee_ids'][0][2], [self.employee_1.id])

    def test_default_get_without_active_ids(self):
        wizard = self.env['employee.transfer.wizard'].default_get(
            ['employee_ids'])
        self.assertNotIn('employee_ids', wizard)

    def test_transfer_single_employee(self):
        wizard = self.env['employee.transfer.wizard'].create({
            'employee_ids': [(6, 0, [self.employee_1.id])],
            'target_company_id': self.company_2.id,
        })
        action = wizard.action_transfer_employees()
        transferred_ids = action['domain'][0][2]
        self.assertEqual(len(transferred_ids), 1)
        new_emp = self.env['hr.employee'].browse(transferred_ids[0])
        self.assertEqual(new_emp.name, 'Test employee 1')
        self.assertEqual(new_emp.company_id.id, self.company_2.id)

    def test_second_transfer_after_first_raises_error(self):
        self.wizard.archive_option = False
        self.wizard.action_transfer_employees()
        wizard2 = self.env['employee.transfer.wizard'].create({
            'employee_ids': [(6, 0, [self.employee_1.id])],
            'target_company_id': self.company_2.id,
        })
        with self.assertRaises(ValidationError):
            wizard2.action_transfer_employees()

    def test_forbidden_fields_are_not_copied(self):
        self.wizard.action_transfer_employees()
        new_employee = self.env['hr.employee'].search([
            ('name', '=', 'Test employee 1'),
            ('company_id', '=', self.company_2.id),
        ])
        self.assertFalse(new_employee.parent_id)
        self.assertFalse(new_employee.coach_id)

    def test_archive_option_archives_original_and_transfers_user(self):
        self.wizard.action_transfer_employees()
        new_employee = self.env['hr.employee'].search([
            ('name', '=', 'Test employee 1'),
            ('company_id', '=', self.company_2.id),
        ])
        self.assertEqual(new_employee.user_id.id, self.employee_user.id)
        self.assertFalse(self.employee_1.active)
        self.assertFalse(self.employee_1.user_id)

    def test_company_context_on_creation(self):
        target_env = self.env['hr.employee'].with_company(self.company_2)
        data = self.wizard._get_employee_data_for_copy(self.employee_1, [])
        new_emp = target_env.create(data)
        self.assertEqual(new_emp.company_id.id, self.company_2.id)
        self.assertEqual(new_emp.name, 'Test employee 1')

    def test_m2o_fields_are_converted_for_creation(self):
        data = self.wizard._get_employee_data_for_copy(self.employee_1, [])
        self.assertIsInstance(data['address_home_id'], int)
        new_emp = self.env['hr.employee'].with_company(self.company_2).create(data)
        self.assertEqual(new_emp.address_home_id.id, self.employee_address.id)

    def test_additional_field_ids_domain_filter(self):
        field = self.env['ir.model.fields'].create({
            'name': 'x_test_field',
            'model_id': self.env['ir.model']._get('hr.employee').id,
            'field_description': 'Test Field',
            'ttype': 'char',
            'store': True,
        })
        wizard = self.env['employee.transfer.wizard'].create({
            'employee_ids': [(6, 0, [self.employee_1.id])],
            'target_company_id': self.company_2.id,
        })
        wizard.additional_field_ids = [(4, field.id)]
        wizard.action_transfer_employees()
        new_emp = self.env['hr.employee'].search([
            ('name', '=', 'Test employee 1'),
            ('company_id', '=', self.company_2.id),
        ])
        self.assertEqual(new_emp.x_test_field, False)

    def test_copy_data_returns_all_fields(self):
        vals = self.wizard._get_employee_data_for_copy(
            self.employee_1, ['work_phone'])
        self.assertIn('name', vals)
        self.assertIn('company_id', vals)
        self.assertIn('work_email', vals)
        self.assertIn('work_phone', vals)
        self.assertIn('user_id', vals)
        self.assertNotIn('parent_id', vals)
        self.assertNotIn('coach_id', vals)
