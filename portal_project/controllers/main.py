###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import io
import json
from collections import OrderedDict

import xlsxwriter
from markupsafe import Markup
from odoo import _, fields, http
from odoo.addons.portal.controllers.portal import CustomerPortal
from odoo.addons.portal.controllers.portal import pager as portal_pager
from odoo.exceptions import AccessError, MissingError
from odoo.http import content_disposition, request
from odoo.osv.expression import AND, OR


class CustomerPortal(CustomerPortal):
    _closed_task_stage_names = ('Done', 'Cancelled')
    _project_task_items_per_page = 50

    def _project_get_page_view_values(
            self, project, access_token, page=1, date_begin=None,
            date_end=None, sortby=None, search=None, search_in='content',
            groupby=None, **kwargs):
        items_per_page = self._items_per_page
        self._items_per_page = self._project_task_items_per_page
        try:
            domain = [('project_id', '=', project.id)]
            filterby = kwargs.get('filterby', 'active_tasks')
            domain += self._get_task_filter_domain(project, filterby)
            url = '/my/projects/%s' % project.id
            values = self._prepare_tasks_values(
                page, date_begin, date_end, sortby, search, search_in,
                groupby, url, domain, su=bool(access_token))
            values['pager']['url_args']['access_token'] = access_token
            if kwargs.get('filterby'):
                values['pager']['url_args']['filterby'] = kwargs['filterby']
            pager = portal_pager(**values['pager'])
            values.update(
                grouped_tasks=values['grouped_tasks'](pager['offset']),
                page_name='project',
                pager=pager,
                project=project,
                task_url='projects/%s/task' % project.id)
            if not groupby:
                values['groupby'] = 'none'
            return self._get_page_view_values(
                project, access_token, values, 'my_projects_history', False,
                **kwargs)
        finally:
            self._items_per_page = items_per_page

    def _get_active_task_domain(self, task_field=False):
        prefix = '%s.' % task_field if task_field else ''
        return [
            ('%sis_closed' % prefix, '=', False),
            '|',
            ('%sstage_id' % prefix, '=', False),
            ('%sstage_id.name' % prefix, 'not in',
             self._closed_task_stage_names),
        ]

    def _get_task_filter_domain(self, project, filterby):
        if filterby == 'active_tasks':
            return self._get_active_task_domain()
        if filterby == 'all':
            return []
        date_from = fields.Datetime.from_string('%s-01-01 00:00:00' % filterby)
        date_to = fields.Datetime.from_string('%s-12-31 23:59:59' % filterby)
        return [
            ('create_date', '>=', date_from),
            ('create_date', '<=', date_to),
        ]

    def _project_get_search_domain(self, search_in, search):
        search_domain = []
        if search_in in ('content', 'all'):
            search_domain.append([('name', 'ilike', search)])
            search_domain.append([('description', 'ilike', search)])
        if search_in in ('customer', 'all'):
            search_domain.append([('partner_id', 'ilike', search)])
        if search_in in ('message', 'all'):
            search_domain.append([('message_ids.body', 'ilike', search)])
        if search_in in ('ref', 'all'):
            search_domain.append([('id', 'ilike', search)])
        if search_in in ('milestone', 'all'):
            search_domain.append([('milestone_ids', 'ilike', search)])
        if search_in in ('users', 'all'):
            user_ids = request.env['res.users'].sudo().search([(
                'name',
                'ilike',
                search)])
            search_domain.append([('user_id', 'in', user_ids.ids)])
        return OR(search_domain)

    def _project_get_searchbar_inputs(self, milestones_allowed):
        values = {
            'all': {'input': 'all', 'label': _('Search in All'), 'order': 1},
            'content': {'input': 'content', 'label': Markup(
                _('Search <span class="nolabel"> (in Content)</span>')),
                'order': 1},
            'users': {'input': 'users', 'label': _('Search in Assignees'),
                      'order': 3},
            'message': {'input': 'message', 'label': _('Search in Messages'),
                        'order': 11},
        }
        if milestones_allowed:
            values['milestone'] = {'input': 'milestone',
                                   'label': _('Search in Milestone'),
                                   'order': 6}

        return dict(sorted(values.items(), key=lambda item: item[1]["order"]))

    @http.route()
    def portal_my_projects(self, page=1, date_begin=None, date_end=None,
                           sortby=None, **kw):
        res = super().portal_my_projects(
            page=page, date_begin=date_begin, date_end=date_end, sortby=sortby,
            **kw)
        Project = request.env['project.project']
        Project_sudo = Project.sudo()
        domain = []
        search = kw.get('search') or None
        search_in = kw.get('search_in') or 'content'
        if search_in and search:
            domain += self._project_get_search_domain(search_in, search)
        milestone_domain = AND([None, [('allow_milestones', '=', 'True')]])
        milestones_allowed = Project.sudo().search_count(
            milestone_domain, limit=1) == 1
        searchbar_inputs = self._project_get_searchbar_inputs(
            milestones_allowed)
        searchbar_sortings = res.qcontext['searchbar_sortings']
        order = searchbar_sortings['date']['order']
        pager = res.qcontext['pager']
        projects = Project.search(domain, order=order, offset=pager['offset'])
        res.qcontext['searchbar_inputs'] = searchbar_inputs
        res.qcontext['pager']['total'] = Project_sudo.search_count(domain),
        res.qcontext['search'] = search
        res.qcontext['search_in'] = search_in,
        res.qcontext['projects'] = projects
        return res

    @http.route()
    def portal_my_project(
        self, project_id=None, access_token=None, page=1, date_begin=None,
        date_end=None, sortby=None, search=None, search_in='content',
            groupby=None, task_id=None, **kw):
        groupby = groupby or 'none'
        res = super().portal_my_project(
            project_id=project_id, access_token=access_token, page=page,
            date_begin=date_begin, date_end=date_end, sortby=sortby,
            search=search, search_in=search_in, groupby=groupby,
            task_id=task_id, **kw)
        if not getattr(res, 'qcontext', None) or 'project' not in res.qcontext:
            return res
        project = res.qcontext['project']
        if not project.allow_timesheets:
            return res
        searchbar_filters, year_to = self.get_year_searchbar_filters(
            project.date_start, project.create_date)
        domain = [
            ('project_id', '=', int(project_id)),
            ('task_id', '!=', False),
        ]
        filterby = kw.get('filterby', 'active_tasks')
        if filterby != 'all':
            domain.extend(searchbar_filters[filterby]['domain'])
        timesheets = request.env['account.analytic.line'].sudo().search(domain)
        res.qcontext['project_timesheet_count'] = len(timesheets)
        values = {}
        res.qcontext['period_unit_amount'] = 0
        for timesheet in timesheets:
            if filterby != 'all':
                key = '%s / %s' % (
                    fields.Datetime.from_string(timesheet.date).year,
                    str(fields.Datetime.from_string(
                        timesheet.date).month).zfill(2))
            else:
                key = '%s' % (
                    fields.Datetime.from_string(timesheet.date).year)
            values.setdefault(key, 0)
            values[key] += timesheet.unit_amount
            res.qcontext['period_unit_amount'] += timesheet.unit_amount
        res.qcontext['period_unit_amount_avg'] = (
            res.qcontext['period_unit_amount'] / len(values)
            if res.qcontext['period_unit_amount'] != 0 else 0)
        values = OrderedDict(sorted(values.items()))
        res.qcontext['searchbar_filters'] = OrderedDict(sorted(
            searchbar_filters.items()))
        res.qcontext['filterby'] = filterby
        res.qcontext['default_url'] = '/my/projects/%s' % project_id
        res.qcontext['graph_data'] = json.dumps([{
            'key': _('Spent time per month (in hours)'),
            'values': [{'text': k, 'count': v} for k, v in values.items()],
        }])
        return res

    def get_year_searchbar_filters(
            self, project_date_start, project_date_create):
        year_to = fields.Datetime.from_string(fields.Datetime.now()).year
        year_from = fields.Datetime.from_string(
            project_date_start
            or project_date_create).year
        searchbar_filters = {
            'active_tasks': {
                'label': _('Active tasks'),
                'domain': self._get_active_task_domain('task_id'),
            },
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
        return searchbar_filters, year_to

    @http.route(
        ['/my/unit/timesheets/<int:project_id>'], type='http', auth='user',
        website=True)
    def portal_my_timesheets_unit(self, project_id, **kw):
        try:
            self._document_check_access('project.project', project_id)
        except (AccessError, MissingError):
            return request.redirect('/my')
        portal_values = self._prepare_portal_layout_values()
        project = request.env['project.project'].browse(project_id)
        searchbar_filters, year_to = self.get_year_searchbar_filters(
            project.date_start, project.create_date)
        domain = [
            ('project_id', '=', int(project_id)),
            ('task_id', '!=', False),
        ]
        filterby = kw.get('filterby', str(year_to))
        if filterby != 'all':
            domain.extend(searchbar_filters[filterby]['domain'])
        timesheets = request.env['account.analytic.line'].sudo().search(
            domain, order='date desc')
        portal_values.update({
            'default_url': '/my/unit/timesheets/%s' % project_id,
            'filterby': filterby,
            'page_name': 'timesheets',
            'project_id': project_id,
            'project_name': project.name,
            'searchbar_filters': OrderedDict(
                sorted(searchbar_filters.items())),
            'timesheets': timesheets,
        })
        return request.render(
            'portal_project.portal_my_timesheets', portal_values)

    @http.route([
        '/my/unit/timesheets/<int:project_id>/export',
    ], type='http', auth='user', website=True)
    def portal_my_timesheets_export(self, project_id, **kw):
        try:
            self._document_check_access('project.project', project_id)
        except (AccessError, MissingError):
            return request.redirect('/my')
        project = request.env['project.project'].browse(project_id)
        searchbar_filters, year_to = self.get_year_searchbar_filters(
            project.date_start, project.create_date)
        domain = [
            ('project_id', '=', int(project_id)),
            ('task_id', '!=', False),
        ]
        filterby = kw.get('filterby', str(year_to))
        if filterby != 'all':
            domain.extend(searchbar_filters[filterby]['domain'])
        timesheets = request.env['account.analytic.line'].sudo().search(
            domain, order='date desc')
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet()
        title_format = workbook.add_format({
            'align': 'left',
            'bg_color': '#e0e0e0',
            'font_name': 'Liberation Sans',
            'valign': 'vjustify',
        })
        cell_format = workbook.add_format({
            'align': 'left',
            'font_name': 'Liberation Sans',
            'valign': 'vjustify',
        })
        cell_format_right = workbook.add_format({
            'align': 'right',
            'font_name': 'Liberation Sans',
            'valign': 'vjustify',
        })
        sheet.write('A1', _('Timesheet #'), title_format)
        sheet.write('B1', _('Date'), title_format)
        sheet.write('C1', _('Assigned to'), title_format)
        sheet.write('D1', _('Description'), title_format)
        sheet.write('E1', _('Task'), title_format)
        sheet.write('F1', _('Duration'), title_format)
        sheet.set_column('A:A', 15)
        sheet.set_column('B:B', 15)
        sheet.set_column('C:C', 30)
        sheet.set_column('D:D', 30)
        sheet.set_column('E:E', 30)
        sheet.set_column('F:F', 10)
        position = 2
        for timesheet in timesheets:
            sheet.write('A' + str(position), timesheet.id, cell_format)
            sheet.write('B' + str(position), timesheet.date.strftime(
                '%d/%m/%Y'), cell_format)
            sheet.write(
                'C' + str(position), timesheet.sudo().employee_id.name,
                cell_format)
            sheet.write('D' + str(position), timesheet.name, cell_format)
            sheet.write(
                'E' + str(position), timesheet.task_id.name, cell_format)

            sheet.write(
                'F' + str(position), timesheet.unit_amount,
                cell_format_right)
            position += 1
        workbook.close()
        output.seek(0)
        response = request.make_response(
            output.read(),
            headers=[
                ('Content-Type', 'application/vnd.ms-excel'),
                ('Content-Disposition',
                    content_disposition('timesheets.xlsx')),
            ])
        output.close()
        return response
