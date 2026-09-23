###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase


class TestProductCodeUniqueMulticompany(TransactionCase):

    def setUp(self):
        super().setUp()
        self.main_company = self.env.ref('base.main_company')
        self.new_company = self.env['res.company'].create({
            'name': 'New test company',
        })
        self.new_user = self.env['res.users'].create({
            'name': 'Test user',
            'login': 'user@test.com',
            'company_ids': [
                (6, 0, [self.main_company.id, self.new_company.id])],
            'company_id': self.main_company.id,
            'groups_id': [(6, 0, [
                self.env.ref('base.group_system').id,
            ])],
        })
        self.new_user.partner_id.email = self.new_user.login

    def test_product_code_unique_multicompany(self):
        self.env['product.product'].sudo(
            self.new_user.id).create({
                'type': 'service',
                'company_id': self.main_company.id,
                'name': 'Test service product (company 1)',
                'default_code': 'TEST-CODE',
                'standard_price': 10,
                'list_price': 100,
            })
        self.new_user.company_id = self.new_company.id
        self.env['product.product'].sudo(
            self.new_user.id).create({
                'type': 'service',
                'company_id': self.new_company.id,
                'name': 'Test service product (company 2)',
                'default_code': 'TEST-CODE',
                'standard_price': 20,
                'list_price': 200,
            })
        with self.assertRaises(ValidationError) as result:
            self.env['product.product'].sudo(
                self.new_user.id).create({
                    'type': 'service',
                    'company_id': self.main_company.id,
                    'name': 'Test service product (company 1)',
                    'default_code': 'TEST-CODE',
                    'standard_price': 20,
                    'list_price': 200,
                })
        self.assertIn(
            'The internal reference TEST-CODE already exists in another '
            'product for this company. It must be unique!',
            result.exception.args[0])

    def test_product_code_unique_only_one_company(self):
        self.new_user.company_ids = [(6, 0, [self.main_company.id])],
        self.env['product.product'].sudo(
            self.new_user.id).create({
                'type': 'service',
                'company_id': self.main_company.id,
                'name': 'Test service product (company 1)',
                'default_code': 'TEST-CODE',
                'standard_price': 10,
                'list_price': 100,
            })
        with self.assertRaises(ValidationError) as result:
            self.env['product.product'].sudo(
                self.new_user.id).create({
                    'type': 'service',
                    'company_id': self.main_company.id,
                    'name': 'New test service product (company 1)',
                    'default_code': 'TEST-CODE',
                    'standard_price': 20,
                    'list_price': 200,
                })
        self.assertIn(
            'The internal reference TEST-CODE already exists in another '
            'product for this company. It must be unique!',
            result.exception.args[0])

    def test_product_code_unique_only_without_company(self):
        self.new_user.company_ids = [(6, 0, [self.main_company.id])],
        self.env['product.product'].sudo(
            self.new_user.id).create({
                'type': 'service',
                'company_id': False,
                'name': 'Test service product (company empty)',
                'default_code': 'TEST-CODE',
                'standard_price': 10,
                'list_price': 100,
            })
        with self.assertRaises(ValidationError) as result:
            self.env['product.product'].sudo(
                self.new_user.id).create({
                    'type': 'service',
                    'company_id': False,
                    'name': 'New test service product (company empty)',
                    'default_code': 'TEST-CODE',
                    'standard_price': 20,
                    'list_price': 200,
                })
        self.assertIn(
            'The internal reference TEST-CODE already exists in another '
            'product for this company. It must be unique!',
            result.exception.args[0])
