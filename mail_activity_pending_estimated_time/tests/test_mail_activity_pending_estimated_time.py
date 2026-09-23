###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests.common import TransactionCase


class TestMailActivityPendingEstimatedTime(TransactionCase):

    def setUp(self):
        super().setUp()
        self.project = self.env['project.project'].create({
            'name': 'Test Project',
        })
        self.task = self.env['project.task'].create({
            'name': 'Test Task',
            'project_id': self.project.id,
        })
        self.activity_type = self.env.ref('mail.mail_activity_data_todo')
        self.model_task_id = self.env['ir.model']._get('project.task').id

    def test_action_open_origin_record(self):
        activity = self.env['mail.activity'].create({
            'res_id': self.task.id,
            'res_model_id': self.model_task_id,
            'activity_type_id': self.activity_type.id,
        })
        action = activity.action_open_origin_record()
        self.assertEqual(action.get('res_id'), self.task.id)
        self.assertEqual(action.get('res_model'), 'project.task')
        self.assertEqual(action.get('type'), 'ir.actions.act_window')
        self.assertEqual(action.get('view_mode'), 'form')

    def test_compute_pending_estimated_time(self):
        self.assertEqual(self.task.pending_estimated_time, 0)
        activity_1 = self.env['mail.activity'].create({
            'res_id': self.task.id,
            'res_model_id': self.model_task_id,
            'activity_type_id': self.activity_type.id,
            'pending_estimated_time': 1.5,
        })
        self.task.invalidate_model(['pending_estimated_time'])
        self.assertEqual(self.task.pending_estimated_time, 1.5)
        activity_2 = self.env['mail.activity'].create({
            'res_id': self.task.id,
            'res_model_id': self.model_task_id,
            'activity_type_id': self.activity_type.id,
            'pending_estimated_time': 2.75,
        })
        self.task.invalidate_model(['pending_estimated_time'])
        self.assertEqual(self.task.pending_estimated_time, 4.25)
        activity_1.write({
            'pending_estimated_time': 1,
        })
        self.task.invalidate_model(['pending_estimated_time'])
        self.assertEqual(self.task.pending_estimated_time, 3.75)
        activity_2.unlink()
        self.task.invalidate_model(['pending_estimated_time'])
        self.assertEqual(self.task.pending_estimated_time, 1)
