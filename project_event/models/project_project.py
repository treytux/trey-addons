###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class ProjectProject(models.Model):
    _inherit = 'project.project'

    event_count = fields.Integer(
        string='Event count',
        compute='_compute_event_count',
    )
    event_ids = fields.One2many(
        comodel_name='event.event',
        inverse_name='project_id',
        string='Events',
    )
    event_line_ids = fields.One2many(
        comodel_name='project.event.line',
        inverse_name='project_id',
        string='Event line generator',
    )
    product_line_ids = fields.One2many(
        comodel_name='project.product.line',
        inverse_name='project_id',
        string='Product line',
    )
    not_modify_event = fields.Boolean(
        related='project_status.not_modify_event',
    )

    def write(self, vals):
        re = super().write(vals)
        if 'project_status' in vals and self.project_status.not_modify_event:
            for project in self:
                project.generate_events()
        return re

    @api.depends('event_ids')
    def _compute_event_count(self):
        for project in self:
            project.event_count = len(project.event_ids)

    def generate_events(self):
        self.ensure_one()
        for line in self.event_line_ids:
            if line.event_ids:
                continue
            line.generate_events()

    @api.multi
    def action_event_view(self):
        action = self.env.ref('event.action_event_view').read()[0]
        action['context'] = {
            'default_project_id': self.id,
        }
        action['domain'] = [('project_id', 'in', self.ids)]
        return action
