###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests import HttpCase


class TestPortalProjectTaskWorkorder(HttpCase):

    def setUp(self):
        super().setUp()
        self.company = self.env.company
        self.location_center = self.env['stock.location'].create({
            'name': 'Center A',
            'usage': 'internal',
        })
        self.project = self.env['project.project'].create({
            'name': 'Workorder Project',
        })
        self.company.workorders_project = self.project
        self.stage_new = self.env['project.task.type'].create({
            'name': 'New',
        })
        self.stage_done = self.env['project.task.type'].create({
            'name': 'Done',
        })
        self.project.type_ids = [self.stage_new.id, self.stage_done.id]
        self.authenticate('admin', 'admin')

    def test_portal_creation_flow(self):
        self.company.workorders_project = False
        res = self.url_open('/my/create_workorder_form',
                            data={'name': 'fail', })
        self.assertTrue(res.url.endswith('/shop'))
        self.company.workorders_project = self.project
        payload = {
            'name': 'Test Workorder',
            'description': 'Description text',
            'center_locations': self.location_center.id,
        }
        self.url_open('/my/create_workorder_form', data=payload)
        task = self.env['project.task'].search([
            ('name', '=', 'Test Workorder'),
        ], limit=1)
        self.assertEqual(task.center.id, self.location_center.id)
        self.assertTrue(task.portal_created)

    def test_write_logic(self):
        task = self.env['project.task'].create({
            'name': 'Mail Test',
            'project_id': self.project.id,
            'portal_created': True,
            'workorder_create_user': self.env.user.id,
            'stage_id': self.stage_new.id,
        })
        self.env['mail.mail'].search([]).unlink()
        task.write({
            'stage_id': self.stage_done.id,
        })
        mail = self.env['mail.mail'].search([
            ('res_id', '=', task.id),
        ])
        mail.unlink()
        task.write({
            'name': 'New Name',
        })
        self.assertEqual(len(self.env['mail.mail'].search([])), 0)
