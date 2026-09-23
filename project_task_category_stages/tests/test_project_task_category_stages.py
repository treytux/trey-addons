###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests.common import TransactionCase


class TestProjectEventStock(TransactionCase):
    def setUp(self):
        super().setUp()
        self.project_type_support = self.env['project.type'].create({
            'name': 'Technical support',
        })
        self.project_type_sales = self.env['project.type'].create({
            'name': 'Sales',
        })
        self.project_type_others = self.env['project.type'].create({
            'name': 'Others',
        })
        self.project_task_type_open = self.env['project.task.type'].create({
            'name': 'Open',
            'case_default': True,
            'project_type_ids': [(6, 0, [
                self.project_type_support.id,
                self.project_type_sales.id,
                self.project_type_others.id,
            ])],
        })
        self.project_task_type_repair = self.env['project.task.type'].create({
            'name': 'Repair',
            'case_default': True,
            'project_type_ids': [(4, self.project_type_support.id)]
        })
        self.project_task_type_review = self.env['project.task.type'].create({
            'name': 'Review',
            'case_default': True,
            'project_type_ids': [(4, self.project_type_sales.id)]
        })
        self.project_task_type_done = self.env['project.task.type'].create({
            'name': 'Done',
            'case_default': True,
            'project_type_ids': [(6, 0, [
                self.project_type_support.id,
                self.project_type_sales.id,
                self.project_type_others.id,
            ])],
        })
        self.project_task_type_manual = self.env['project.task.type'].create({
            'name': 'Manual',
            'case_default': False,
            'project_type_ids': [(6, 0, [
                self.project_type_support.id,
                self.project_type_sales.id,
                self.project_type_others.id,
            ])],
        })

    def test_project_support_default_stages(self):
        project_support = self.env['project.project'].create({
            'name': 'Project test support',
            'type_id': self.project_type_support.id,
        })
        project_support._onchange_type_id()
        self.assertIn(self.project_task_type_open, project_support.type_ids)
        self.assertIn(self.project_task_type_repair, project_support.type_ids)
        self.assertNotIn(
            self.project_task_type_review, project_support.type_ids)
        self.assertIn(self.project_task_type_done, project_support.type_ids)
        self.assertNotIn(
            self.project_task_type_manual, project_support.type_ids)

    def test_project_sales_default_stages(self):
        project_sales = self.env['project.project'].create({
            'name': 'Project test sales',
            'type_id': self.project_type_sales.id,
        })
        project_sales._onchange_type_id()
        self.assertIn(self.project_task_type_open, project_sales.type_ids)
        self.assertNotIn(
            self.project_task_type_repair, project_sales.type_ids)
        self.assertIn(self.project_task_type_review, project_sales.type_ids)
        self.assertIn(self.project_task_type_done, project_sales.type_ids)
        self.assertNotIn(
            self.project_task_type_manual, project_sales.type_ids)

    def test_project_others_default_stages(self):
        project_others = self.env['project.project'].create({
            'name': 'Project test others',
            'type_id': self.project_type_others.id,
        })
        project_others._onchange_type_id()
        self.assertIn(self.project_task_type_open, project_others.type_ids)
        self.assertNotIn(
            self.project_task_type_repair, project_others.type_ids)
        self.assertNotIn(
            self.project_task_type_review, project_others.type_ids)
        self.assertIn(self.project_task_type_done, project_others.type_ids)
        self.assertNotIn(
            self.project_task_type_manual, project_others.type_ids)
