###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import json
from collections import OrderedDict

from odoo import _, fields
from odoo.addons.portal.controllers.portal import CustomerPortal
from odoo.addons.portal.controllers.portal import pager as portal_pager
from odoo.http import request, route


class CustomerPortal(CustomerPortal):
    def _prepare_portal_layout_values(self):
        values = super(CustomerPortal, self)._prepare_portal_layout_values()
        Employee = request.env['hr.employee']
        employee_count = Employee.search_count([
            (
                'active',
                '=',
                True,
            ),
        ])
        values.update({
            'employee_count': employee_count,
        })
        return values

    @route(
        ['/my/employees'],
        type='http',
        auth='user',
        website=True,
    )
    def portal_my_employees(
            self, page=1, date_begin=None, date_end=None, sortby=None, **kw):
        values = self._prepare_portal_layout_values()
        Employee = request.env['hr.employee']
        domain = [
            (
                'active',
                '=',
                True,
            ),
        ]
        searchbar_sortings = {
            'name': {'label': _('Title'), 'order': 'name'},
            # 'date': {'label': _('Order Date'), 'order': 'date_order desc'},
            # 'stage': {'label': _('Stage'), 'order': 'state'},
        }
        if not sortby:
            sortby = 'name'
        sort_order = searchbar_sortings[sortby]['order']
        archive_groups = self._get_archive_groups('hr.employee', domain)
        if date_begin and date_end:
            domain += [
                ('create_date', '>', date_begin),
                ('create_date', '<=', date_end),
            ]
        employee_count = Employee.search_count(domain)
        pager = portal_pager(
            url='/my/employees',
            url_args={
                'date_begin': date_begin,
                'date_end': date_end,
                'sortby': sortby
            },
            total=employee_count,
            page=page,
            step=self._items_per_page
        )
        employees = Employee.search(
            domain, order=sort_order, limit=self._items_per_page,
            offset=pager['offset'])
        request.session['my_employees_history'] = employees.ids[:100]
        values.update({
            'date': date_begin,
            'employees': employees.sudo(),
            'page_name': 'contract',
            'pager': pager,
            'archive_groups': archive_groups,
            'default_url': '/my/employees',
            'searchbar_sortings': searchbar_sortings,
            'sortby': sortby,
        })
        return request.render(
            'portal_hr.portal_my_employees', values)

    @route(
        ['/my/employee/<int:employee_id>'], type='http', auth='user',
        website=True, csrf=False)
    def portal_my_employee(self, employee_id, **kw):
        employee = request.env['hr.employee'].browse(employee_id)
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
                        ('date', '>=', date_from),
                        ('date', '<=', date_to),
                    ],
                }
            })
        domain = [('employee_id', '=', employee_id)]
        filterby = kw.get('filterby', str(year_to))
        if filterby != 'all':
            domain.extend(searchbar_filters[filterby]['domain'])
        timesheets = request.env['account.analytic.line'].search(domain)
        values = {}
        unit_amount_total = 0
        real_time_total = 0
        for timesheet in timesheets:
            key = '%s / %s' % (
                fields.Datetime.from_string(timesheet.date).year,
                str(fields.Datetime.from_string(
                    timesheet.date).month).zfill(2))
            # key = '%s' % (
            #     fields.Datetime.from_string(timesheet.date).year)
            values.setdefault(key, 0)
            values[key] += timesheet.unit_amount
            unit_amount_total += timesheet.unit_amount
            real_time_total += timesheet.real_time
        values = OrderedDict(sorted(values.items()))
        timesheets_avg = values and unit_amount_total / len(values) or 0
        real_time_avg = values and real_time_total / len(values) or 0
        timesheets_data = json.dumps([{
            'key': _('Worked time per month (in hours)'),
            'values': [{'text': k, 'count': v} for k, v in values.items()],
        }])
        # timesheets_data = [{
        #     'key': 'Partes de horas',
        #     'values': [
        #         {'text': '2020 / 01', 'count': 15.583333333333332},
        #         {'text': '2020 / 02', 'count': 14.016666666666673},
        #         {'text': '2020 / 03', 'count': 7.816666666666666},
        #         {'text': '2020 / 04', 'count': 8.3},
        #         {'text': '2020 / 05', 'count': 11.036666666666669}
        #     ]}]
        assigned_tasks = [{
            'key': 'Tareas asignadas',
            'values': [
                {'text': '2020 / 01', 'count': 15.583333333333332},
                {'text': '2020 / 02', 'count': 14.016666666666673},
                {'text': '2020 / 03', 'count': 7.816666666666666},
                {'text': '2020 / 04', 'count': 8.3},
                {'text': '2020 / 05', 'count': 11.036666666666669}
            ]}]
        values = self._get_page_view_values(
            employee,
            False,
            {
                'page_name': 'employee',
                'employee': employee.sudo(),
                'timesheets_avg': timesheets_avg,
                'real_time_avg': real_time_avg,
                'timesheets_data': timesheets_data,
                'tasks_data': assigned_tasks,
                'user': request.env.user,
                'searchbar_filters': OrderedDict(sorted(searchbar_filters.items())),
                'filterby': filterby,
                'default_url': '/my/employee/%s' % employee.id,
            },
            'my_employees_history',
            False,
            **kw
        )
        return request.render('portal_hr.portal_my_employee', values)
