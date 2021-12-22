###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests.common import HttpCase


class TestAuthToken(HttpCase):

    def setUp(self):
        super().setUp()
        self.company = self.env['res.company'].create({
            'name': 'Test company',
        })
        self.portal_user = self.env['res.users'].create({
            'name': 'Test Portal User',
            'login': 'portal@mail.com',
            'company_ids': [(6, 0, [self.company.id])],
            'company_id': self.company.id,
            'groups_id': [(6, 0, [
                    self.env.ref('base.group_portal').id,
            ])],
        })
        self.public_user = self.env['res.users'].create({
            'name': 'Test Public User',
            'login': 'public@mail.com',
            'company_ids': [(6, 0, [self.company.id])],
            'company_id': self.company.id,
            'groups_id': [(6, 0, [
                    self.env.ref('base.group_public').id,
            ])],
        })
        self.internal_user = self.env['res.users'].create({
            'name': 'Test Internal User',
            'login': 'internal@mail.com',
            'company_ids': [(6, 0, [self.company.id])],
            'company_id': self.company.id,
            'groups_id': [(6, 0, [
                self.env.ref('base.group_user').id,
            ])],
        })

    def test_login_user_not_found(self):
        website = self.env['website'].get_current_website()
        self.assertEqual(website.token_access, 'external_users')
        token = 'xxxxx'
        response = self.url_open('/token/%s' % token)
        self.assertEqual(response.status_code, 500)

    def test_auth_token_internal_user_all_users_login_ok(self):
        website = self.env['website'].get_current_website()
        self.assertEqual(website.token_access, 'external_users')
        website.token_access = 'all_users'
        self.assertEqual(website.token_access, 'all_users')
        self.assertFalse(self.internal_user.share)
        self.assertTrue(self.internal_user.token)
        self.internal_user.password = self.internal_user.token
        response = self.url_open('/token/%s' % self.internal_user.token)
        self.assertEqual(response.status_code, 200)

    def test_auth_token_portal_user_all_users_login_ok(self):
        website = self.env['website'].get_current_website()
        self.assertEqual(website.token_access, 'external_users')
        website.token_access = 'all_users'
        self.assertEqual(website.token_access, 'all_users')
        self.assertTrue(self.portal_user.share)
        self.assertTrue(self.portal_user.token)
        self.portal_user.password = self.portal_user.token
        response = self.url_open('/token/%s' % self.portal_user.token)
        self.assertEqual(response.status_code, 200)

    def test_auth_token_public_user_all_users_login_ok(self):
        website = self.env['website'].get_current_website()
        self.assertEqual(website.token_access, 'external_users')
        website.token_access = 'all_users'
        self.assertEqual(website.token_access, 'all_users')
        self.assertTrue(self.public_user.share)
        self.assertTrue(self.public_user.token)
        self.public_user.password = self.public_user.token
        response = self.url_open('/token/%s' % self.public_user.token)
        self.assertEqual(response.status_code, 200)

    def test_login_internal_user_only_external_users(self):
        website = self.env['website'].get_current_website()
        self.assertEqual(website.token_access, 'external_users')
        self.assertFalse(self.internal_user.share)
        self.assertTrue(self.internal_user.token)
        self.internal_user.password = self.internal_user.token
        response = self.url_open('/token/%s' % self.internal_user.token)
        self.assertEqual(response.status_code, 500)

    def test_login_public_user_only_external_users(self):
        website = self.env['website'].get_current_website()
        self.assertEqual(website.token_access, 'external_users')
        self.assertTrue(self.public_user.share)
        self.assertTrue(self.public_user.token)
        self.public_user.password = self.public_user.token
        response = self.url_open('/token/%s' % self.public_user.token)
        self.assertEqual(response.status_code, 200)

    def test_login_portal_user_only_external_users(self):
        website = self.env['website'].get_current_website()
        self.assertEqual(website.token_access, 'external_users')
        self.assertTrue(self.portal_user.share)
        self.assertTrue(self.portal_user.token)
        self.portal_user.password = self.portal_user.token
        response = self.url_open('/token/%s' % self.portal_user.token)
        self.assertEqual(response.status_code, 200)

    def test_login_internal_user_only_internal_users(self):
        website = self.env['website'].get_current_website()
        self.assertEqual(website.token_access, 'external_users')
        website.token_access = 'internal_users'
        self.assertEqual(website.token_access, 'internal_users')
        self.assertFalse(self.internal_user.share)
        self.assertTrue(self.internal_user.token)
        self.internal_user.password = self.internal_user.token
        response = self.url_open('/token/%s' % self.internal_user.token)
        self.assertEqual(response.status_code, 200)

    def test_login_public_user_only_internal_users(self):
        website = self.env['website'].get_current_website()
        self.assertEqual(website.token_access, 'external_users')
        website.token_access = 'internal_users'
        self.assertEqual(website.token_access, 'internal_users')
        self.assertTrue(self.public_user.share)
        self.assertTrue(self.public_user.token)
        self.public_user.password = self.public_user.token
        response = self.url_open('/token/%s' % self.public_user.token)
        self.assertEqual(response.status_code, 500)

    def test_login_portal_user_only_internal_users(self):
        website = self.env['website'].get_current_website()
        self.assertEqual(website.token_access, 'external_users')
        website.token_access = 'internal_users'
        self.assertEqual(website.token_access, 'internal_users')
        self.assertTrue(self.portal_user.share)
        self.assertTrue(self.portal_user.token)
        self.portal_user.password = self.portal_user.token
        response = self.url_open('/token/%s' % self.portal_user.token)
        self.assertEqual(response.status_code, 500)
