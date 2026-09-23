###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.addons.portal_employee.controllers.portal import EmployeeWebsite
from odoo.tests import TransactionCase


class TestEmployeeKnowledgeCompany(TransactionCase):

    def setUp(self):
        super().setUp()
        self.controller = EmployeeWebsite()
        self.parent_company = self.env['res.company'].create({
            'name': 'Parent Knowledge Company',
        })
        self.employee_company = self.env['res.company'].create({
            'name': 'Employee Knowledge Company',
            'parent_id': self.parent_company.id,
        })
        self.other_company = self.env['res.company'].create({
            'name': 'Other Knowledge Company',
        })
        self.employee = self.env['hr.employee'].create({
            'name': 'Knowledge Employee',
            'company_id': self.employee_company.id,
        })

    def _create_page(self, company):
        return self.env['document.page'].create({
            'name': company and company.name or 'Global Knowledge',
            'type': 'category',
            'company_id': company and company.id or False,
        })

    def test_employee_knowledge_company_ids_include_parent_companies(self):
        company_ids = self.controller._get_employee_knowledge_company_ids(
            self.employee)
        self.assertIn(self.employee_company.id, company_ids)
        self.assertIn(self.parent_company.id, company_ids)
        self.assertNotIn(self.other_company.id, company_ids)

    def test_employee_knowledge_allows_global_company(self):
        page = self._create_page(False)
        self.assertTrue(
            self.controller._is_employee_knowledge_company_allowed(
                page, self.employee))

    def test_employee_knowledge_allows_employee_company(self):
        page = self._create_page(self.employee_company)
        self.assertTrue(
            self.controller._is_employee_knowledge_company_allowed(
                page, self.employee))

    def test_employee_knowledge_allows_parent_company(self):
        page = self._create_page(self.parent_company)
        self.assertTrue(
            self.controller._is_employee_knowledge_company_allowed(
                page, self.employee))

    def test_employee_knowledge_rejects_other_company(self):
        page = self._create_page(self.other_company)
        self.assertFalse(
            self.controller._is_employee_knowledge_company_allowed(
                page, self.employee))
