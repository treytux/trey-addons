###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.exceptions import UserError
from odoo.tests import TransactionCase


class TestWarningProject(TransactionCase):

    def setUp(self):
        super().setUp()
        self.partner = self.env['res.partner'].create({
            'name': 'Test Partner',
        })
        self.project = self.env['project.project'].create({
            'name': 'Test Project',
        })
        self.task = self.env['project.task'].create({
            'name': 'Test Task',
            'project_id': self.project.id,
        })

    def test_task_warning_mode(self):
        self.partner.write({
            'task_warn': 'warning',
            'task_warn_msg': 'Warning message test',
        })
        self.task.partner_id = self.partner
        result = self.task.onchange_partner_id()
        self.assertIn('warning', result)
        self.assertEqual(result['warning']['message'], 'Warning message test')

    def test_task_block_mode(self):
        self.partner.write({
            'task_warn': 'block',
            'task_warn_msg': 'Block message test',
        })
        self.task.partner_id = self.partner
        with self.assertRaises(UserError):
            self.task.onchange_partner_id()
