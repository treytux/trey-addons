###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class ProjectTask(models.Model):
    _inherit = 'project.task'

    vote_ids = fields.One2many(
        string='Votes',
        comodel_name='project.task.vote',
        inverse_name='task_id',
    )
    is_valuable = fields.Boolean(
        string='It is valuable',
    )
    voting = fields.Float(
        string='Voting',
        compute='_compute_voting',
    )

    @api.depends('vote_ids')
    def _compute_voting(self):
        for task in self:
            task.voting = sum([v.vote for v in task.vote_ids if v.vote != -1])
