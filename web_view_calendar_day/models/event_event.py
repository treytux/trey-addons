###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from datetime import date, datetime, timedelta

from odoo import fields, models
from pytz import timezone


class EventEvent(models.Model):
    _inherit = 'event.event'

    address_name = fields.Char(
        related='address_id.name',
        string='Address name',
    )
    address_total_ids = fields.Many2many(
        string='Total locations',
        comodel_name='res.partner',
        relation='partners2event_rel',
        column1='event_id',
        column2='partner_id',
        compute='_compute_total_addresses',
    )
    is_preproduction = fields.Boolean(
        string='Pre-production',
    )
    calendar_view_color = fields.Char(
        string='Calendar view color',
        compute='_compute_calendar_view_color',
    )

    def _compute_total_addresses(self):
        for event in self:
            event.address_total_ids = (
                event.address_id.ids + event.address_ids.ids)

    def _compute_calendar_view_color(self):
        default_color = '#3d86ac'
        for event in self:
            if not event.project_id or not event.project_id.analytic_account_id:
                event.calendar_view_color = default_color
                continue
            event.calendar_view_color = (
                event.project_id.analytic_account_id.calendar_color
                or default_color)

    def _clean_date_domain(self, domain):
        separator = ' GMT' in domain and ' GMT' or '.'
        domain = datetime.strptime(
            domain.split(separator)[0].replace(' ', '').replace('T', ''),
            '%Y-%m-%d%H:%M:%S')
        return domain

    def get_events_day(self, domain):
        locations = self.env['res.partner'].search([
            ('partner_category', '=', 'event_location'),
            ('parent_id', '!=', False),
            ('show_in_calendar', '=', True),
        ])
        context = self.env.context.copy()
        context_date_str = context.get('date', False)
        date_start_present = any('date_begin' in element for element in domain)
        date_end_present = any('date_end' in element for element in domain)
        if context_date_str:
            context['date'] = False
            self.env.context = context
            hour_splitted = context_date_str.split('Z')
            context_date = datetime.strptime(hour_splitted[0], '%Y-%m-%d')
            date_begin = context_date + timedelta(hours=int(hour_splitted[1]))
            domain = [
                ['date_begin', '<=', date_begin + timedelta(days=1)],
                ['date_end', '>=', date_begin],
                ['state', '!=', 'cancel'],
            ]
        elif not date_start_present and not date_end_present:
            user_tz = timezone(self.env.user.tz or 'UTC')
            date_begin = datetime.combine(
                date.today(), datetime.min.time()).replace(tzinfo=user_tz)
            domain.insert(len(domain) - 1, '&')
            domain.append(['date_begin', '<=', date_begin + timedelta(days=1)])
            domain.append(['date_end', '>=', date_begin])
        elif not date_start_present:
            for count, element in enumerate(domain):
                if 'date_end' in element:
                    domain[count][2] = self._clean_date_domain(domain[count][2])
                    domain.insert(count + 1, [
                        'date_begin', '<=', domain[count][2]
                        + timedelta(days=1)])
        elif not date_end_present:
            for count, element in enumerate(domain):
                if 'date_begin' in element:
                    domain[count][2] = self._clean_date_domain(domain[count][2])
                    domain.insert(count, [
                        'date_end', '<=', domain[count][2]
                        + timedelta(days=1)])
        else:
            for count, element in enumerate(domain):
                if 'date_begin' in element:
                    domain[count][2] = self._clean_date_domain(domain[count][2])
                if 'date_end' in element:
                    domain[count][2] = self._clean_date_domain(domain[count][2])
        events = self.search(domain, order='date_begin')
        locations_dict = {}
        for location in locations:
            locations_dict.setdefault(location.name, [])
            location_events = events.filtered(
                lambda ev: location.id in ev.address_total_ids.ids)
            extra_location_events = events.filtered(
                lambda ev: ev.address_id.id in location.extra_address_ids.ids)
            for location_event in location_events:
                other_addresses = extra_location_events.filtered(
                    lambda ev: ev.address_id.id
                    in location_event.address_id.extra_address_ids.ids
                ) and 'yes' or 'no'
                locations_dict[location.name].append({
                    'address_id': location,
                    'address_name': location_event.address_name,
                    'state': location_event.state,
                    'date_begin': location_event.date_begin,
                    'date_end': location_event.date_end,
                    'calendar_view_color': location_event.calendar_view_color,
                    'id': location_event.id,
                    'is_online': location_event.is_online,
                    'name': location_event.name,
                    'is_preproduction': location_event.is_preproduction,
                    'other_addresses': other_addresses,
                })
        return locations_dict
