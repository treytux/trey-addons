###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class ProjectGroup(models.Model):
    _name = 'project.group'
    _description = 'Projects group'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'sequence, id'

    name = fields.Char(
        required=True,
        translate=True,
    )
    project_ids = fields.One2many(
        string='Projects',
        comodel_name='project.project',
        inverse_name='project_group_id',
    )
    user_id = fields.Many2one(
        comodel_name='res.users',
        string='Responsible',
        default=lambda self: self.env.user,
    )
    sequence = fields.Integer(
        default=1,
    )
    short_description = fields.Text(
        string='Short Description',
        translate=True,
    )
    description = fields.Text(
        translate=True,
    )
    project_count = fields.Integer(
        compute='_compute_project_count',
        string='# Projects'
    )

    def _compute_project_count(self):
        for group in self:
            group.project_count = self.env['project.project'].search_count(
                [('project_group_id', '=', group.id)])

    def action_view_project(self):
        for group in self:
            projects = self.env['project.project'].search([
                ('project_group_id', '=', group.id),
            ])
            action = self.env.ref(
                'project_groups.action_group_project').read()[0]
            action['context'] = {}
            if len(projects) == 1:
                action['views'] = [(
                    self.env.ref('project.edit_project').id, 'form')]
                action['res_id'] = projects.ids[0]
            else:
                action['domain'] = [('id', 'in', projects.ids)]
            return action
