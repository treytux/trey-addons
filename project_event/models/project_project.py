###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from datetime import datetime, time, timedelta

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class ProjectProject(models.Model):
    _inherit = 'project.project'

    @api.model
    def _get_default_date_start(self):
        return datetime.combine(
            fields.Date.today(), time.min) - timedelta(
                hours=int(self.env.user.tz_offset[:3]))

    @api.model
    def _get_default_date_end(self):
        return datetime.combine(
            fields.Date.today(), time.max) - timedelta(
                hours=int(self.env.user.tz_offset[:3]))

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
        domain=[('product_type', '!=', 'service')],
    )
    service_line_ids = fields.One2many(
        comodel_name='project.product.line',
        inverse_name='project_id',
        string='Service line',
        domain=[('product_type', '=', 'service')],
    )
    not_modify_event = fields.Boolean(
        related='project_status.not_modify_event',
    )
    date_start = fields.Datetime(
        string='Start date',
        copy=False,
        default=_get_default_date_start,
    )
    date_end = fields.Datetime(
        string='End date',
        copy=False,
        default=_get_default_date_end,
    )
    address_id = fields.Many2one(
        comodel_name='res.partner',
        string='Location',
    )

    def write(self, vals):
        re = super().write(vals)
        if 'project_status' in vals:
            for project in self.filtered(lambda p: p.not_modify_event):
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

    @api.constrains('date_start', 'date_end')
    def _check_project_dates(self):
        msg = _('The closing date cannot be earlier than the beginning date.')
        for project in self:
            if not project.date_start or not project.date_end:
                continue
            if project.date_end < project.date_start:
                raise ValidationError(msg)
