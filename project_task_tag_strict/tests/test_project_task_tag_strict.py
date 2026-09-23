###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests import common


class TestProjectTaskTagStrict(common.TransactionCase):

    def setUp(self):
        super().setUp()
        self.partner = self.env['res.partner'].create({
            'name': 'Test partner',
            'is_company': True,
        })
        self.project = self.env['project.project'].create({
            'name': 'Project test',
            'partner_id': self.partner.id,
        })
        self.task = self.env['project.task'].create({
            'name': 'Test task',
            'project_id': self.project.id,
            'partner_id': self.partner.id,
            'user_id': self.env.ref('base.user_demo').id,
        })
        self.tag_01 = self.env['project.tags'].create({
            'name': 'Tag test 1',
        })
        self.tag_02 = self.env['project.tags'].create({
            'name': 'Tag test 2',
        })
        self.tag_03 = self.env['project.tags'].create({
            'name': 'Tag test 3',
        })

    def test_check_tags_available(self):
        self.assertEqual(len(self.project.tag_ids), 0)
        self.assertEqual(len(self.task.tag_ids), 0)
        self.assertEqual(len(self.task.domain_tag_ids), 0)
        self.project.write({
            'tag_ids': [(6, 0, [
                self.tag_01.id, self.tag_02.id, self.tag_03.id])],
        })
        self.assertEqual(len(self.project.tag_ids), 3)
        self.assertEqual(len(self.task.domain_tag_ids), 3)
        self.task.write({
            'tag_ids': [(6, 0, [
                self.tag_01.id, self.tag_02.id, self.tag_03.id])],
        })
        self.assertEqual(len(self.task.tag_ids), 3)
        self.project.write({
            'tag_ids': [(3, self.tag_03.id)],
        })
        self.project.check_task_tags()
        self.assertEqual(len(self.project.tag_ids), 2)
        self.assertIn(self.tag_01.id, self.project.tag_ids.ids)
        self.assertIn(self.tag_02.id, self.project.tag_ids.ids)
        self.assertNotIn(self.tag_03.id, self.project.tag_ids.ids)
        self.assertEqual(len(self.task.domain_tag_ids), 2)
        self.assertEqual(len(self.task.tag_ids), 2)
        self.assertIn(self.tag_01.id, self.task.tag_ids.ids)
        self.assertIn(self.tag_02.id, self.task.tag_ids.ids)
        self.assertNotIn(self.tag_03.id, self.task.tag_ids.ids)
