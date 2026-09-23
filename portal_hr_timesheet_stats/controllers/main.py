###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import calendar
import json
from collections import OrderedDict

from odoo import _, fields, http
from odoo.addons.portal.controllers.portal import CustomerPortal
from odoo.http import request


class CustomerPortal(CustomerPortal):
    def get_weekend_days(self, year, month):
        total_days = calendar.monthrange(year, month)[1]
        weekend_days = 0
        for day in range(1, total_days + 1):
            day_of_week = calendar.weekday(year, month, day)
            if day_of_week == 5 or day_of_week == 6:
                weekend_days += 1
        return weekend_days

    def get_ets_searchbar_filters(self):
        year_to = fields.Datetime.from_string(fields.Datetime.now()).year
        year_from = 2014
        searchbar_filters = {
            'all': {'label': _('All'), 'domain': []},
        }
        for year in range(year_from, year_to + 1):
            date_from = fields.Datetime.from_string('%s-01-01 00:00:00' % year)
            date_to = fields.Datetime.from_string('%s-12-31 23:59:59' % year)
            searchbar_filters.update({
                str(year): {
                    'label': year,
                    'domain': [
                        ('date_time', '>=', date_from),
                        ('date_time', '<=', date_to),
                    ],
                }
            })
        return searchbar_filters

    def get_productivity(
            self, year, month, number_of_days_display, day_hours, hours):
        working_days = calendar.monthrange(year, month)[1]
        non_working_days = (
            self.get_weekend_days(year, month) + number_of_days_display)
        return 100 / ((working_days - non_working_days) * day_hours) * hours

    @http.route(
        ['/my/stats_employees'], type='http', auth='user',
        website=True)
    def portal_my_stats_employees(self, **kw):
        user = request.env.user
        if not user._is_admin():
            return request.redirect('/my')
        portal_values = self._prepare_portal_layout_values()
        searchbar_sortings = {
            'name': {'label': _('Name'), 'order': 'name'},
        }
        sortby = kw.get('sortby', 'name')
        order = searchbar_sortings[sortby]['order']
        employees = request.env['hr.employee'].sudo().search(
            [
                ('active', '=', True),
            ], order=order)
        portal_values.update({
            'page_name': 'stats_employees',
            'searchbar_sortings': searchbar_sortings,
            'sortby': sortby,
            'employees': employees,
        })
        return request.render(
            'portal_hr_timesheet_stats.portal_my_stats_employees',
            portal_values)

    @http.route(
        ['/my/stats_employee/<int:employee_id>'],
        type='http', auth='user', website=True)
    def portal_my_stats_employee(self, employee_id, **kw):
        if not request.env.user._is_admin():
            return request.redirect('/my')
        portal_values = self._prepare_portal_layout_values()
        employee = request.env['hr.employee'].browse(int(employee_id))
        day_hours = employee.resource_calendar_id.hours_per_day
        searchbar_filters = self.get_ets_searchbar_filters()
        now = fields.Datetime.now()
        filterby = kw.get('filterby', str(now.year))
        year_from = filterby == 'all' and '2014' or filterby
        year_to = filterby == 'all' and str(now.year) or filterby
        month_from = '1'
        month_to = '12'
        date_from = fields.Datetime.from_string(
            '%s-%s-01 00:00:00' % (year_from, month_from))
        date_to = fields.Datetime.from_string(
            '%s-%s-31 23:59:59' % (year_to, month_to))
        leaves = request.env['hr.leave'].sudo().search(
            [
                ('employee_id', '=', int(employee_id)),
                ('state', '=', 'validate'),
                ('date_from', '>=', date_from),
                ('date_to', '<=', date_to),
            ])
        number_of_days_display = sum([
            leave.number_of_days_display for leave in leaves])
        leave_timesheet_task_id = (
            employee.company_id.leave_timesheet_task_id
            and employee.company_id.leave_timesheet_task_id.id
            or False)
        domain = [
            ('employee_id', '=', int(employee_id)),
            ('task_id', 'not in', [
                False, leave_timesheet_task_id]),
        ]
        if filterby != 'all':
            domain.extend(searchbar_filters[filterby]['domain'])
        timesheets = request.env['account.analytic.line'].sudo().search(
            domain, order='date desc')
        time_values = {}
        for timesheet in timesheets:
            year = fields.Datetime.from_string(timesheet.date).year
            month = fields.Datetime.from_string(timesheet.date).month
            key = '%s / %s' % (
                year,
                str(month).zfill(2))
            time_values.setdefault(key, {
                'period': '',
                'unit_amount': 0,
                'real_time': 0,
                'working_days': 0,
                'get_weekend_days': 0,
                'number_of_days_display': 0,
                'longest_amount': 0,
                'longest_real': 0,
                'number_of_days_display_avg': 0,
                'productivity': 0,
                'real_productivity': 0,
            })
            time_values[key]['period'] = key
            time_values[key]['unit_amount'] += timesheet.unit_amount
            time_values[key]['real_time'] += timesheet.real_time
            time_values[key]['working_days'] = calendar.monthrange(
                year, month)[1]
            time_values[key]['get_weekend_days'] = self.get_weekend_days(
                year, month)
            time_values[key]['number_of_days_display'] = number_of_days_display
            time_values[key]['longest_amount'] = (
                time_values[key]['longest_amount'] < timesheet.unit_amount
                and timesheet.unit_amount
                or time_values[key]['longest_amount'])
            time_values[key]['longest_real'] = (
                time_values[key]['longest_real'] < timesheet.real_time
                and timesheet.real_time
                or time_values[key]['longest_real'])
        for timesheet in timesheets:
            year = fields.Datetime.from_string(timesheet.date).year
            month = fields.Datetime.from_string(timesheet.date).month
            key = '%s / %s' % (
                year,
                str(month).zfill(2))
            time_values[key]['number_of_days_display_avg'] = (
                number_of_days_display / len(time_values))
            time_values[key]['productivity'] = self.get_productivity(
                year, month, time_values[key]['number_of_days_display_avg'],
                day_hours, time_values[key]['unit_amount'])
            time_values[key]['real_productivity'] = self.get_productivity(
                year, month, time_values[key]['number_of_days_display_avg'],
                day_hours, time_values[key]['real_time'])
        time_values = OrderedDict(sorted(time_values.items()))
        unit_amount_avg = 0
        real_time_avg = 0
        productivity_avg = 0
        real_productivity_avg = 0
        if time_values:
            for tv in time_values:
                unit_amount_avg += time_values[tv]['unit_amount']
                real_time_avg += time_values[tv]['real_time']
                productivity_avg += time_values[tv]['productivity']
                real_productivity_avg += time_values[tv]['real_productivity']
            unit_amount_avg = unit_amount_avg / len(time_values)
            real_time_avg = real_time_avg / len(time_values)
            productivity_avg = productivity_avg / len(time_values)
            real_productivity_avg = real_productivity_avg / len(time_values)
        values = {
            'labels': [],
            'datasets': [],
        }
        values['labels'] = [time_values[tv]['period'] for tv in time_values]
        values['datasets'].append({
            'label': _('Productivity'),
            'backgroundColor': '#ffcd00',
            'data': [time_values[tv]['productivity'] for tv in time_values],
            'stack': 'Stack 0',
        })
        values['datasets'].append({
            'label': _('Real'),
            'backgroundColor': '#6cc24a',
            'data': [
                time_values[tv]['real_productivity'] for tv in time_values],
            'stack': 'Stack 1',
        })
        portal_values.update({
            'chart_data': json.dumps(values),
            'default_url': '/my/stats_employee/%s' % employee_id,
            'employee': employee,
            'employee_id': employee_id,
            'filterby': filterby,
            'page_name': 'stats_employee',
            'productivity_avg': productivity_avg,
            'real_productivity_avg': real_productivity_avg,
            'real_time_avg': real_time_avg,
            'searchbar_filters': OrderedDict(sorted(searchbar_filters.items())),
            'timesheets': timesheets,
            'time_values': time_values,
            'unit_amount_avg': unit_amount_avg,
        })
        return request.render(
            'portal_hr_timesheet_stats.portal_my_stats_employee',
            portal_values)
