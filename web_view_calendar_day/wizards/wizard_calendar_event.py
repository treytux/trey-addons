###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import json
from datetime import datetime, timedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class WizardCalendarEvent(models.TransientModel):
    _name = 'wizard.calendar.event'
    _description = 'Wizard to create events or projects from calendar day'

    option = fields.Selection(
        selection=[
            ('project_event', 'New project and event'),
            ('event', 'Event for an existing project'),
            ('internal', 'Internal booking'),
        ],
        string='Type',
        default='project_event',
        required=True,
    )
    name = fields.Char(
        string='Event name',
        required=True,
    )
    start_booking = fields.Datetime(
        string='Start booking',
        required=True,
    )
    end_booking = fields.Datetime(
        string='End booking',
        required=True,
    )
    address_ids = fields.Many2many(
        string='Addresses',
        comodel_name='res.partner',
        relation='calendar_event_partner_rel',
        column1='wizard_calendar_event_id',
        column2='res_partner_id',
        required=True,
    )
    project_id = fields.Many2one(
        comodel_name='project.project',
        string='Project',
    )
    start_activity = fields.Datetime(
        string='Start activity',
        required=True,
    )
    end_activity = fields.Datetime(
        string='End activity',
        required=True,
    )
    project_type = fields.Many2one(
        comodel_name='project.type',
        string='Project type',
    )

    @api.constrains('start_booking', 'start_activity')
    def _constraint_start_times(self):
        datetime_min_limit = datetime.strptime('06:00', '%H:%M') - timedelta(
            hours=int(self.env.user.tz_offset[:3]))
        for rec in self:
            if rec.start_booking.time() < datetime_min_limit.time():
                raise UserError(_('Minimum start booking time is 07:00'))
            if rec.start_activity.time() < datetime_min_limit.time():
                raise UserError(_('Minimum start activity time is 07:00'))

    def generate_event_prepare(self, date_start, date_end, preproduction):
        self.ensure_one()
        vals = {
            'name': self.name,
            'address_id': self.address_ids and self.address_ids[0].id or False,
            'address_ids': [(6, 0, self.address_ids[1:].ids)],
            'date_begin': date_start,
            'date_end': date_end,
            'is_preproduction': preproduction,
        }
        if self.project_id:
            vals['project_id'] = self.project_id.id
        return vals

    def generate_project_prepare(self, date_start, date_end):
        self.ensure_one()
        return {
            'name': self.name,
            'address_id': self.address_ids and self.address_ids[0].id or False,
            'address_ids': [(6, 0, self.address_ids[1:].ids)],
            'date_start': date_start,
            'date_end': date_end,
            'type_id': self.project_type.id,
        }

    def button_create(self):
        events = self.env['event.event']
        project_obj = self.env['project.project']
        project = False
        events |= events.create(self.generate_event_prepare(
            self.start_activity or self.start_booking,
            self.end_activity or self.end_booking, False))
        if self.start_activity and self.start_booking < self.start_activity:
            events |= events.create(self.generate_event_prepare(
                self.start_booking, self.start_activity, True))
        if self.end_activity and self.end_activity < self.end_booking :
            events |= events.create(self.generate_event_prepare(
                self.end_activity, self.end_booking, True))
        if self.option == 'project_event':
            project = project_obj.create(self.generate_project_prepare(
                self.start_booking, self.end_booking))
            events.write({
                'project_id': project.id
            })
        action = self.env.ref('event.action_event_view').read()[0]
        action_context = json.loads(action['context'])
        action_context['date'] = self.env.context['default_start_activity']
        action['context'] = str(action_context)
        action['views'] = [(
            self.env.ref('web_view_calendar_day.event_event_calendar_day').id,
            'calendar_day',
        )]
        return action
