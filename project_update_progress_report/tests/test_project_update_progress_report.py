###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests.common import TransactionCase


class TestProjectUpdateProgressReport(TransactionCase):

    def setUp(self):
        super().setUp()
        self.company = self.env['res.company'].create({
            'name': 'Test Company',
        })
        self.partner = self.env['res.partner'].create({
            'name': 'Test Partner',
        })
        self.manager = self.env['res.users'].create({
            'name': 'Test Manager',
            'login': 'test_manager',
        })
        self.stage = self.env['project.project.stage'].create({
            'name': 'Test Stage',
        })
        self.project_standard = self.env['project.project'].create({
            'name': 'Test Project',
            'company_id': self.company.id,
            'partner_id': self.partner.id,
            'user_id': self.manager.id,
            'stage_id': self.stage.id,
            'allow_billable': True,
            'is_template': False,
        })
        self.project_template = self.env['project.project'].create({
            'name': 'Template Project',
            'is_template': True,
        })
        self.update_standard_1 = self.env['project.update'].create({
            'name': 'Standard Update 1',
            'project_id': self.project_standard.id,
            'progress': 40,
            'status': 'on_track',
        })
        self.update_standard_2 = self.env['project.update'].create({
            'name': 'Standard Update 2',
            'project_id': self.project_standard.id,
            'progress': 80,
            'status': 'at_risk',
        })
        self.update_template = self.env['project.update'].create({
            'name': 'Template Update',
            'project_id': self.project_template.id,
            'progress': 50,
            'status': 'on_track',
        })

    def test_view_creates_and_excludes_templates(self):
        reports = self.env['project.update.progress.report'].search([])
        report_project_ids = reports.mapped('project_id.id')
        self.assertIn(self.project_standard.id, report_project_ids)
        self.assertNotIn(self.project_template.id, report_project_ids)

    def test_status_uses_correct_selection(self):
        report_model = self.env['project.update.progress.report']
        update_model = self.env['project.update']
        report_selection = (
            report_model._fields['status']._description_selection(self.env))
        update_selection = (
            update_model._fields['status']._description_selection(self.env))
        method_selection = report_model._get_selection_values_for_status()
        self.assertEqual(report_selection, update_selection)
        self.assertEqual(method_selection, update_selection)

    def test_project_fields_mapping(self):
        report = self.env['project.update.progress.report'].search([
            ('project_id', '=', self.project_standard.id),
            ('progress', '=', 40),
        ], limit=1)
        self.assertTrue(report)
        self.assertEqual(report.company_id.id, self.company.id)
        self.assertEqual(report.partner_id.id, self.partner.id)
        self.assertEqual(report.stage_id.id, self.stage.id)
        self.assertEqual(report.project_manager_id.id, self.manager.id)
        self.assertEqual(report.allow_billable, True)

    def test_progress_groups_as_max(self):
        result = self.env['project.update.progress.report'].read_group(
            domain=[('project_id', '=', self.project_standard.id)],
            fields=['project_id', 'progress'],
            groupby=['project_id'])
        self.assertTrue(result)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['progress'], 80)
