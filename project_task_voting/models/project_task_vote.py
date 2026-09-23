###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class ProjectTaskVote(models.Model):
    _name = 'project.task.vote'
    _description = 'Project task vote'

    user_id = fields.Many2one(
        comodel_name='res.users',
        string='User',
        default=lambda self: self.env.user,
        readonly=True,
        required=True,
    )
    vote = fields.Selection(
        string='Vote',
        selection=[
            (-1, 'No vote'),
            (1, 'Low'),
            (2, 'Medium'),
            (3, 'High'),
        ],
        default=-1,
    )
    vote_date = fields.Datetime(
        string='Vote date',
        readonly=True,
    )
    task_stage_id = fields.Many2one(
        comodel_name='project.task.type',
        string='Task stage',
        readonly=True,
    )
    task_id = fields.Many2one(
        comodel_name='project.task',
        string='Task',
        readonly=True,
    )
    project_id = fields.Many2one(
        comodel_name='project.project',
        related='task_id.project_id',
        string='Project',
        readonly=True,
    )

    @api.model
    def create(self, vals):
        task = self.env['project.task'].browse(vals.get('task_id', False))
        if not vals.get('task_id', False):
            return super().create(vals)
        vals['task_stage_id'] = task.stage_id.id
        vote = vals.get('vote', False)
        votes = self.search([
            ('user_id', '=', vals.get('user_id', self.env.user.id)),
            ('task_id', '=', vals['task_id']),
            '|',
            ('task_stage_id', '=', task.stage_id.id),
            ('task_stage_id', '=', False),
        ])
        if votes:
            raise ValidationError(
                _('Only can only vote once for each task and stage'))
        if vote < -1:
            raise ValidationError(_('You can not vote negative amounts'))
        return super().create(vals)

    def write(self, vals):
        for rec in self:
            vote = vals.get('vote', False)
            if rec.user_id and rec.user_id.id != self.env.user.id:
                raise ValidationError(_(
                    'Voting on behalf of another person is not allowed'))
            if not vote or rec.vote != -1 or not rec.task_id:
                continue
            if vote < 0:
                raise ValidationError(_('You can not vote negative amounts'))
            if not rec.task_id.stage_id.allow_voting:
                raise ValidationError(
                    _('You can not vote in current task state'))
            vals['vote_date'] = fields.Datetime.now()
            vals['task_stage_id'] = rec.task_id.stage_id.id
            rec.task_id.message_post(body=(
                _('User %s has voted') % rec.user_id.name))
        return super().write(vals)
