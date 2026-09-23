###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests.common import TransactionCase


class PartnerWebsiteLinks(TransactionCase):
    def setUp(self):
        super().setUp()
        self.user_1 = self.env['res.users'].create({
            'name': 'Test User 1',
            'login': 'user1@test.com',
            'email': 'user1@test.com',
            'groups_id': [(6, 0, [
                self.env.ref('partner_website_links.group_website_links_user').id
            ])]
        })
        self.user_2 = self.env['res.users'].create({
            'name': 'Test User 2',
            'login': 'user2@test.com',
            'email': 'user2@test.com',
            'groups_id': [(6, 0, [
                self.env.ref('partner_website_links.group_website_links_user').id
            ])]
        })
        self.partner_1 = self.user_1.partner_id
        self.partner_2 = self.user_2.partner_id
        self.website_link_ids_1 = self.partner_1.website_link_ids
        self.website_link_ids_2 = self.partner_2.website_link_ids

    def log(self, mostrando):
        import logging
        logging.basicConfig(level=logging.INFO)
        logger = logging.getLogger(__name__)
        logger.info(f'Estás mostrando: {mostrando}')

    def create_website_link(self, user, public):
        model = 'res.partner.website.link'
        self.env[model].sudo(user).create({
            'name': 'Test',
            'url': 'https://google.es',
            'user': 'Tests',
            'password': '123456789',
            'is_public': public,
            'partner_id': user.partner_id.id,
        })
        self.website_link_ids_1 = self.partner_1.website_link_ids
        self.website_link_ids_2 = self.partner_2.website_link_ids

    def search_website_link(self, user):
        return self.env['res.partner.website.link'].search([
            '|',
            ('create_uid', '=', user.id),
            ('is_public', '=', True)])

    def test_partner_website_links_public_false(self):
        self.assertEqual(len(self.website_link_ids_1), 0)
        self.create_website_link(self.user_1, False)
        self.assertEqual(len(self.website_link_ids_1), 1)
        self.assertEqual(self.website_link_ids_1.is_public, False)
        self.assertEqual(self.website_link_ids_1.create_uid, self.user_1)
        self.assertEqual(len(self.search_website_link(self.user_1)), 1)
        self.assertEqual(
            self.search_website_link(self.user_1), self.website_link_ids_1)
        self.assertEqual(len(self.search_website_link(self.user_2)), 0)

    def test_partner_website_links_public_true(self):
        self.assertEqual(len(self.website_link_ids_1), 0)
        self.create_website_link(self.user_1, True)
        self.assertEqual(len(self.website_link_ids_1), 1)
        self.assertEqual(self.website_link_ids_1.is_public, True)
        self.assertEqual(self.website_link_ids_1.create_uid, self.user_1)
        self.assertEqual(len(self.search_website_link(self.user_1)), 1)
        self.assertEqual(len(self.search_website_link(self.user_2)), 1)
        self.assertEqual(
            self.search_website_link(self.user_1), self.website_link_ids_1)
        self.assertEqual(
            self.search_website_link(self.user_2), self.website_link_ids_1)
