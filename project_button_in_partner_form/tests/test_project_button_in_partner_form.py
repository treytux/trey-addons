###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests import common


class TestPartnerProjects(common.TransactionCase):

    def setUp(self):
        super(TestPartnerProjects, self).setUp()

        self.company_1 = self.env['res.partner'].create({
            'name': 'Test Company 1',
            'is_company': True,
        })
        self.company_2 = self.env['res.partner'].create({
            'name': 'Test Company 2',
            'is_company': True,
        })
        self.individual = self.env['res.partner'].create({
            'name': 'John Doe',
            'is_company': False,
        })
        self.project_1 = self.env['project.project'].create({
            'name': 'Project Alpha',
            'partner_id': self.company_1.id,
        })
        self.project_2 = self.env['project.project'].create({
            'name': 'Project Beta',
            'partner_id': self.company_1.id,
        })
        self.project_3 = self.env['project.project'].create({
            'name': 'Project Gamma',
            'partner_id': self.company_2.id,
        })

    def test_compute_project_totals_for_company_with_projects(self):
        self.assertEqual(self.company_1.project_totals, 2)
        self.assertEqual(self.company_2.project_totals, 1)

    def test_compute_project_totals_for_company_without_projects(self):
        new_company = self.env['res.partner'].create({
            'name': 'New Company',
            'is_company': True,
        })
        self.assertEqual(new_company.project_totals, 0)

    def test_compute_project_totals_for_individual(self):
        self.assertEqual(self.individual.project_totals, 0)

    def test_compute_project_totals_after_adding_project(self):
        initial_count = self.company_1.project_totals
        self.env['project.project'].create({
            'name': 'Project Delta',
            'partner_id': self.company_1.id,
        })
        self.company_1._compute_project_totals()
        self.assertEqual(self.company_1.project_totals, initial_count + 1)

    def test_compute_project_totals_after_deleting_project(self):
        initial_count = self.company_1.project_totals
        self.project_1.unlink()
        self.company_1._compute_project_totals()
        self.assertEqual(self.company_1.project_totals, initial_count - 1)

    def test_action_view_projects_for_company(self):
        action = self.company_1.action_view_projects()

        self.assertEqual(action['name'], 'Projects')
        self.assertEqual(action['res_model'], 'project.project')
        self.assertEqual(action['type'], 'ir.actions.act_window')
        self.assertEqual(action['view_mode'], 'tree,form')
        self.assertEqual(action['limit'], 80)
        self.assertEqual(
            action['domain'], [('partner_id', '=', self.company_1.id)])
        self.assertEqual(action['context']['default_res_model'], 'res.partner')
        self.assertEqual(
            action['context']['default_res_id'], self.company_1.id)

    def test_action_view_projects_ensure_one(self):
        with self.assertRaises(ValueError):
            (self.company_1 + self.company_2).action_view_projects()

    def test_project_totals_readonly(self):
        field = self.env['res.partner']._fields['project_totals']
        self.assertTrue(field.readonly)

    def test_project_totals_after_transferring_project(self):
        self.project_3.partner_id = self.company_1.id
        self.company_1._compute_project_totals()
        self.company_2._compute_project_totals()
        self.assertEqual(self.company_1.project_totals, 3)
        self.assertEqual(self.company_2.project_totals, 0)

    def test_large_number_of_projects(self):
        company = self.env['res.partner'].create({
            'name': 'Large Test Company',
            'is_company': True,
        })
        for i in range(100):
            self.env['project.project'].create({
                'name': f'Project {i}',
                'partner_id': company.id,
            })
        company._compute_project_totals()
        self.assertEqual(company.project_totals, 100)

    def test_partner_with_special_characters(self):
        special_company = self.env['res.partner'].create({
            'name': 'Test & Company <script>alert("test")</script>',
            'is_company': True,
        })
        self.env['project.project'].create({
            'name': 'Special Project',
            'partner_id': special_company.id,
        })
        special_company._compute_project_totals()
        self.assertEqual(special_company.project_totals, 1)
        action = special_company.action_view_projects()
        self.assertIsNotNone(action)

    def test_empty_partner_list_compute(self):
        empty_partners = self.env['res.partner'].browse([])
        empty_partners._compute_project_totals()
