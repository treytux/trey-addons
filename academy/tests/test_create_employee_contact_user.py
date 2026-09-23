###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from .test_base import TestBase


class TestCreateEmployeeContactUser(TestBase):
    def setUp(self):
        super().setUp()
        self.partner_obj = self.env['res.partner']
        self.employee_obj = self.env['hr.employee']
        self.group_teacher = self.env.ref('academy.group_academy_teacher')
        self.teacher_user = self.env.ref('academy.template_teacher_user')

    def test_create_employee_with_activity_selectable(self):
        employee = self.employee_obj.create({
            'name': 'Selectable Employee',
            'is_activity_selectable': True,
        })
        employee._inverse_work_contact_details()
        self.assertTrue(employee.work_contact_id)
        self.assertTrue(employee.work_contact_id.is_teacher)
        self.assertEqual(employee.work_contact_id.related_employee_id, employee)

    def test_action_create_user_with_activity_selectable(self):
        partner = self.partner_obj.create({
            'name': 'Work Contact Partner',
        })
        employee = self.employee_obj.create({
            'name': 'Selectable Employee',
            'is_activity_selectable': True,
            'work_contact_id': partner.id,
        })
        result = employee.action_create_user()
        self.assertIn('default_groups_id', result['context'])
        self.assertIn('default_partner_id', result['context'])
        group_ids = [g.id for g in self.teacher_user.groups_id]
        self.assertEqual(result['context']['default_groups_id'], group_ids)
        self.assertEqual(result['context']['default_partner_id'], partner.id)
