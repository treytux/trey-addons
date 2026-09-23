###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import SUPERUSER_ID, api, fields, models


class ProjectGroup(models.Model):
    _name = 'project.group'
    _description = 'Projects group'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'sequence, id'

    @api.model
    def _read_group_status_ids(self, statuses, domain, order):
        statuse_ids = statuses._search(
            [], order=order, access_rights_uid=SUPERUSER_ID)
        return statuses.browse(statuse_ids)

    @api.model
    def _get_default_status(self):
        if not self.env.ref('project_groups.project_group_status_open'):
            return False
        return self.env.ref('project_groups.project_group_status_open')

    name = fields.Char(
        required=True,
        translate=True,
    )
    company_id = fields.Many2one(
        string='Company',
        comodel_name='res.company',
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
        string='# Projects',
    )
    project_group_status = fields.Many2one(
        default=_get_default_status,
        comodel_name='project.group.status',
        group_expand='_read_group_status_ids',
        ondelete='restrict',
        string='Status',
        copy=False,
        index=True,
        track_visibility='onchange',
    )
    status_closed = fields.Boolean(
        related='project_group_status.is_closed',
    )
    allow_next_status = fields.Boolean(
        compute='_compute_allow_next_status',
    )

    def get_next_status(self):
        self.ensure_one()
        sequence = self.project_group_status.status_sequence
        return self.env['project.group.status'].search([
            ('status_sequence', '>', sequence),
            ('is_closed', '=', False),
        ], order='status_sequence', limit=1)

    @api.depends('project_group_status')
    def _compute_allow_next_status(self):
        for project_group in self:
            next_status = project_group.get_next_status()
            project_group.allow_next_status = (
                next_status and not next_status.is_closed or False)

    def cancel_project_group(self):
        for project_group in self:
            cancel_status = self.env['project.group.status'].search([
                ('is_closed', '=', True),
            ], order='status_sequence desc', limit=1)
            if cancel_status:
                project_group.project_group_status = cancel_status.id

    def do_next_status(self):
        for project_group in self:
            if not project_group.project_group_status:
                return
            next_status = project_group.get_next_status()
            if next_status:
                project_group.project_group_status = next_status.id

    def reopen_project_group(self):
        self.write({
            'project_group_status': self._get_default_status().id,
        })

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
