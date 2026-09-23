###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import exceptions
from odoo.tests.common import TransactionCase


class TestProjectTaskVotes(TransactionCase):

    def setUp(self):
        super().setUp()
        self.stage_1 = self.env.ref('project.project_stage_1')
        self.partner = self.env['res.partner'].create({
            'name': 'Partner test',
            'supplier': True,
        })
        self.project = self.env['project.project'].create({
            'name': 'Test project',
            'partner_id': self.partner.id,
        })
        self.project_task = self.env['project.task'].create({
            'name': 'Test task',
            'project_id': self.project.id,
            'stage_id': self.stage_1.id,
            'is_valuable': True,
        })

    def create_vote(self, vals):
        return self.env['project.task.vote'].create({
            'user_id': vals.get('user_id', self.env.user.id),
            'vote': vals.get('vote', -1),
            'vote_date': vals.get('vote_date', False),
            'task_stage_id': vals.get('task_stage_id', False),
            'task_id': vals.get('task_id', False),
        })

    def test_project_task_vote(self):
        vote_1 = self.create_vote({
            'task_id': self.project_task.id,
        })
        with self.assertRaises(exceptions.ValidationError) as result:
            vote_1.sudo(self.env.ref('base.user_admin').id).write({
                'vote': 3,
            })
        self.assertEqual(
            result.exception.name,
            'Voting on behalf of another person is not allowed')
        with self.assertRaises(exceptions.ValidationError) as result:
            vote_1.write({
                'vote': 3,
            })
        self.assertEqual(
            result.exception.name, 'You can not vote in current task state')
        self.stage_1.allow_voting = True
        vote_1.write({
            'vote': 3,
        })
        self.assertEquals(self.project_task.voting, 3)
        self.assertEquals(len(self.project_task.vote_ids), 1)
        with self.assertRaises(exceptions.ValidationError) as result:
            self.create_vote({
                'task_id': self.project_task.id,
            })
        self.assertEqual(
            result.exception.name,
            'Only can only vote once for each task and stage')
        self.assertEquals(len(self.project_task.vote_ids), 1)
        self.assertEquals(self.project_task.voting, 3)
        stage_2 = self.env.ref('project.project_stage_2')
        stage_2.allow_voting = True
        self.project_task.stage_id = stage_2
        vote_2 = self.create_vote({
            'task_id': self.project_task.id,
        })
        with self.assertRaises(exceptions.ValidationError) as result:
            vote_2.write({
                'vote': -5,
            })
        self.assertEqual(
            result.exception.name, 'You can not vote negative amounts')
        vote_2.write({
            'vote': 2,
        })
        self.assertEquals(len(self.project_task.vote_ids), 2)
        self.assertEquals(self.project_task.voting, 5)
        vote_2.write({
            'vote': 3,
        })
        self.assertEquals(self.project_task.voting, 5)
