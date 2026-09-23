###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.exceptions import AccessError
from odoo.tests import common


class TestDocumentKnowledgeUserSecurity(common.TransactionCase):

    def setUp(self):
        super().setUp()
        self.group_doc_user = self.env.ref(
            'document_knowledge.group_document_user')
        self.test_user = self.env['res.users'].create({
            'name': 'Test Knowledge User',
            'login': 'test_knowledge_user',
            'groups_id': [(6, 0, [self.group_doc_user.id])],
        })
        self.DocumentPage = self.env['document.page']
        self.DocumentPageHistory = self.env['document.page.history']
        self.DocumentPageDiff = self.env[
            'wizard.document.page.history.show_diff']
        self.DocumentPageMenuCreator = self.env['document.page.create.menu']
        self.sample_page = self.DocumentPage.sudo().create({
            'name': 'Test Page',
            'content': '<p>Test content</p>',
        })
        self.sample_page.sudo().write({'content': '<p>First update</p>'})
        self.sample_page.sudo().write({'content': '<p>Second update</p>'})
        self.histories = self.DocumentPageHistory.sudo().search([
            ('page_id', '=', self.sample_page.id),
        ], order='create_date asc', limit=2)
        if len(self.histories) < 2:
            self.histories = self.DocumentPageHistory.sudo().search([
                ('page_id', '=', self.sample_page.id),
            ], limit=1)
            self.histories += self.DocumentPageHistory.sudo().create({
                'page_id': self.sample_page.id,
                'name': self.sample_page.name,
                'content': '<p>Extra revision</p>',
            })
        self.valid_diff = self.DocumentPageDiff.sudo().with_context(
            active_ids=self.histories.ids
        ).create({})
        self.menu_parent = self.env['ir.ui.menu'].sudo().create({
            'name': 'Test Parent',
        })
        self.valid_menu_creator = self.DocumentPageMenuCreator.sudo(
        ).with_context(
            active_id=self.sample_page.id
        ).create({
            'menu_name': 'Test Menu',
            'menu_parent_id': self.menu_parent.id,
        })

    def test_document_page_read_forbidden(self):
        with self.assertRaises(AccessError):
            self.DocumentPage.with_user(self.test_user).search([
                ('id', '=', self.sample_page.id),
            ], limit=1)

    def test_document_page_create_forbidden(self):
        with self.assertRaises(AccessError):
            self.DocumentPage.with_user(self.test_user).create({
                'name': 'Should not be created',
                'content': '<p>Test</p>',
            })

    def test_document_page_write_forbidden(self):
        with self.assertRaises(AccessError):
            self.sample_page.with_user(self.test_user).write({
                'name': 'Forbidden',
            })

    def test_document_page_unlink_forbidden(self):
        temp_page = self.DocumentPage.sudo().create({
            'name': 'Temp to delete',
            'content': '<p>Temp</p>',
        })
        with self.assertRaises(AccessError):
            temp_page.with_user(self.test_user).unlink()

    def test_history_read_forbidden(self):
        with self.assertRaises(AccessError):
            self.DocumentPageHistory.with_user(self.test_user).search(
                [], limit=1)

    def test_history_create_forbidden(self):
        with self.assertRaises(AccessError):
            self.DocumentPageHistory.with_user(self.test_user).create({
                'page_id': self.sample_page.id,
                'name': 'Test history',
                'content': '<p>History content</p>',
            })

    def test_history_write_forbidden(self):
        with self.assertRaises(AccessError):
            self.histories[0].with_user(self.test_user).write({
                'name': 'Forbidden',
            })

    def test_history_unlink_forbidden(self):
        temp_history = self.DocumentPageHistory.sudo().create({
            'page_id': self.sample_page.id,
            'name': 'Temp history',
            'content': '<p>Temp</p>',
        })
        with self.assertRaises(AccessError):
            temp_history.with_user(self.test_user).unlink()

    def test_diff_read_forbidden(self):
        with self.assertRaises(AccessError):
            self.DocumentPageDiff.with_user(self.test_user).search([], limit=1)

    def test_diff_create_forbidden(self):
        with self.assertRaises(AccessError):
            self.DocumentPageDiff.with_user(self.test_user).create({})

    def test_diff_write_forbidden(self):
        with self.assertRaises(AccessError):
            self.valid_diff.with_user(self.test_user).write({})

    def test_diff_unlink_forbidden(self):
        with self.assertRaises(AccessError):
            self.valid_diff.with_user(self.test_user).unlink()

    def test_menu_creator_read_forbidden(self):
        with self.assertRaises(AccessError):
            self.DocumentPageMenuCreator.with_user(self.test_user).search(
                [], limit=1)

    def test_menu_creator_create_forbidden(self):
        with self.assertRaises(AccessError):
            self.DocumentPageMenuCreator.with_user(
                self.test_user).with_context(
                active_id=self.sample_page.id
            ).create({
                'menu_name': 'Forbidden Menu',
                'menu_parent_id': self.menu_parent.id,
            })

    def test_menu_creator_write_forbidden(self):
        with self.assertRaises(AccessError):
            self.valid_menu_creator.with_user(self.test_user).write({
                'menu_name': 'Changed',
            })

    def test_menu_creator_unlink_forbidden(self):
        with self.assertRaises(AccessError):
            self.valid_menu_creator.with_user(self.test_user).unlink()
