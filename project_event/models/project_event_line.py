###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from datetime import datetime, time, timedelta

from dateutil.relativedelta import relativedelta
from dateutil.rrule import WEEKLY, rrule
from odoo import _, api, exceptions, fields, models
from pytz import UTC, timezone


class ProjectEventLine(models.Model):
    _name = 'project.event.line'
    _description = 'Project event line for generate events'

    @api.model
    def _get_default_date_begin(self):
        context = self.env.context
        model_name = context.get('active_model', False)
        active_id = context.get('active_id', False)
        min_today = datetime.combine(
            fields.Date.today(), time.min) - timedelta(
                hours=int(self.env.user.tz_offset[:3]))
        if not model_name or not active_id:
            return min_today
        project = self.env[model_name].browse(active_id)
        return project.date_start or min_today

    @api.model
    def _get_default_date_end(self):
        context = self.env.context
        model_name = context.get('active_model', False)
        active_id = context.get('active_id', False)
        max_today = datetime.combine(
            fields.Date.today(), time.max) - timedelta(
                hours=int(self.env.user.tz_offset[:3]))
        if not model_name or not active_id:
            return max_today
        project = self.env[model_name].browse(active_id)
        return project.date_end or max_today

    @api.model
    def _get_default_address_id(self):
        context = self.env.context
        model_name = context.get('active_model', False)
        active_id = context.get('active_id', False)
        if not model_name or not active_id:
            return False
        project = self.env[model_name].browse(active_id)
        return project.address_id.id

    project_id = fields.Many2one(
        comodel_name='project.project',
        string='Project',
    )
    address_id = fields.Many2one(
        comodel_name='res.partner',
        string='Location',
        default=_get_default_address_id,
    )
    date_begin = fields.Datetime(
        string='Begin',
        default=_get_default_date_begin,
    )
    date_end = fields.Datetime(
        string='End',
        default=_get_default_date_end,
    )
    repeat = fields.Integer(
        string='Repeats',
        default=1,
        required=True,
    )
    period = fields.Selection(
        selection=[
            ('day', 'Days'),
            ('week', 'Week'),
            ('month', 'Months'),
            ('year', 'Year'),
        ],
        string='Period',
        default='day',
        required=True,
    )
    event_ids = fields.One2many(
        comodel_name='event.event',
        inverse_name='project_event_line_id',
        string='Events',
    )
    days_repeat = fields.Many2many(
        comodel_name='project.event.day',
        string='Days repetition',
    )
    date_end_repeat = fields.Date(
        string='End repetition',
    )

    def check_addresses(self, vals):
        self.ensure_one()
        return True

    def generate_event_prepare(self, vals):
        self.ensure_one()
        return vals

    def generate_event_product_line(self, line):
        return {
            'product_id': line.product_id.id,
            'name': line.name,
            'quantity': line.quantity,
            'user_id': line.user_id.id,
            'address_id': self.address_id.id,
        }

    def get_dst_time(self, datetime_a, datetime_b, tz):
        dstime = datetime_a.astimezone(tz).dst().seconds
        dstime_relative = datetime_b.astimezone(tz).dst().seconds
        if dstime < dstime_relative:
            datetime_b = datetime_b - relativedelta(
                seconds=dstime_relative)
        if dstime > dstime_relative:
            datetime_b = datetime_b + relativedelta(seconds=dstime)
        return datetime_b

    def generate_events(self):

        def get_event_data(line, event_date, tz):
            date_end = (datetime.combine(
                event_date.astimezone(tz).date(),
                line.date_end.time()))
            dst_end_time = self.get_dst_time(line.date_end, date_end, tz)
            data = {
                'project_id': line.project_id.id,
                'project_event_line_id': line.id,
                'address_id': (
                    line.address_id.id or line.project_id.partner_id.id),
                'name': line.project_id.name,
                'date_begin': event_date,
                'date_end': dst_end_time,
            }
            if line.project_id.service_line_ids:
                data['service_line_ids'] = []
                for ln in line.project_id.service_line_ids:
                    line_vals = line.generate_event_product_line(ln)
                    if line_vals:
                        data['service_line_ids'].append((0, 0, line_vals))
            if line.project_id.product_line_ids:
                data['product_line_ids'] = []
                for ln in line.project_id.product_line_ids:
                    line_vals = line.generate_event_product_line(ln)
                    if line_vals:
                        data['product_line_ids'].append((0, 0, line_vals))
            return data

        self.ensure_one()
        if not self.date_begin:
            raise exceptions.ValidationError(_('Event date begin is required'))
        event_obj = self.env['event.event']
        holidays_public_id = (
            self.project_id.type_id
            and self.project_id.type_id.hr_holidays_public_id or False)
        tz = timezone(self.env.user.tz)
        events = event_obj
        holidays = []
        if self.period == 'week':
            start_datetime_tz = self.date_begin.astimezone(tz)
            if (start_datetime_tz.date() != self.date_end.astimezone(tz).date()
                    or self.date_begin.date() != self.date_end.date()):
                raise exceptions.ValidationError(_(
                    'In weekly period start and end date must be in same day'))
            days_seq = sorted([day.sequence for day in self.days_repeat])
            for day in days_seq:
                event_days = rrule(
                    WEEKLY,
                    byweekday=day,
                    dtstart=self.date_begin,
                    until=datetime.combine(self.date_end_repeat, time.max),
                )
                for event_date in event_days:
                    date_start = self.get_dst_time(
                        self.date_begin, event_date, tz)
                    vals = get_event_data(self, date_start, tz)
                    if not self.check_addresses(vals):
                        continue
                    events |= event_obj.create(
                        self.generate_event_prepare(vals))
        else:
            for index in range(0, self.repeat):
                date_end = self.date_end or self.date_begin
                if self.period == 'day':
                    date_begin = self.date_begin + relativedelta(days=index)
                    if holidays_public_id:
                        date_tz = date_begin.replace(
                            tzinfo=UTC).astimezone(tz).date()
                        if holidays_public_id.is_public_holiday(date_tz):
                            holidays.append(date_tz.strftime("%m/%d/%Y"))
                            continue
                    date_end = date_end + relativedelta(days=index)
                elif self.period == 'month':
                    date_begin = self.date_begin + relativedelta(months=index)
                    date_end = date_end + relativedelta(months=index)
                elif self.period == 'year':
                    date_begin = self.date_begin + relativedelta(years=index)
                    date_end = date_end + relativedelta(years=index)
                if tz:
                    date_begin = self.get_dst_time(
                        self.date_begin, date_begin, tz)
                    date_end = self.get_dst_time(self.date_end, date_end, tz)
                vals = get_event_data(self, date_begin, tz)
                if not self.check_addresses(vals):
                    continue
                events |= event_obj.create(self.generate_event_prepare(vals))
        if not events:
            raise exceptions.ValidationError(_(
                'It has not been possible to generate events, check dates and '
                'holidays: %s') % (', '.join(holidays)))
        return events

    def action_view_events(self):
        self.ensure_one()
        action = self.env.ref('event.action_event_view').read()[0]
        action['context'] = {
            'default_project_event_line_id': self.id,
        }
        return action
