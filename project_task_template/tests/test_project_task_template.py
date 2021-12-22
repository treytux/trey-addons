###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests import common


class TestProjectTaskTemplate(common.TransactionCase):

    def setUp(self):
        super().setUp()
        self.test_customer = self.env['res.partner'].create({
            'name': 'TestCustomer',
        })
        self.test_project = self.env['project.project'].create({
            'name': 'TestProject',
            'alias_name': 'test_alias',
            'partner_id': self.test_customer.id,
        })
        self.test_task = self.env['project.task'].create({
            'name': 'TestTask',
            'project_id': self.test_project.id,
            'partner_id': self.test_customer.id,
            'user_id': self.env.ref('base.user_demo').id,
        })

    def test_create_task_from_template(self):
        task = self.test_task
        task.is_template = True
        task.create_task_from_template()
        new_task = self.env['project.task'].search([
            ('name', '=', 'TestTask'),
            ('is_template', '=', False),
        ])
        self.assertEqual(len(new_task), 1)
        self.assertEqual(new_task.user_id, task.user_id)
        self.assertFalse(new_task.partner_id)

    def test_create_task_from_template_non_standard_name(self):
        task = self.test_task
        task.is_template = True
        task.name = 'TestTask(Test)'
        task.create_task_from_template()
        new_task = self.env['project.task'].search([
            ('name', '=', 'TestTask(Test)'),
            ('is_template', '=', False),
        ])
        self.assertEqual(len(new_task), 1)
        self.assertEqual(new_task.user_id, task.user_id)
        self.assertFalse(new_task.partner_id)
