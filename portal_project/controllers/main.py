###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import io
import json
from collections import OrderedDict
from operator import itemgetter

import xlsxwriter
from odoo import _, fields, http
from odoo.addons.portal.controllers.portal import CustomerPortal
from odoo.addons.portal.controllers.portal import pager as portal_pager
from odoo.exceptions import AccessError, MissingError
from odoo.http import content_disposition, request
from odoo.osv.expression import OR
from odoo.tools import groupby as groupbyelem


class CustomerPortal(CustomerPortal):
    @http.route(
        ['/my/projects/search'], type='http', auth='public', website=True)
    def portal_projects_search(self, sortby=None, **post):
        project_name = post.get('name')
        searchbar_sortings = {
            'date': {'label': _('Newest'), 'order': 'create_date desc'},
            'name': {'label': _('Name'), 'order': 'name'},
        }
        if not sortby:
            sortby = 'date'
        order = searchbar_sortings[sortby]['order']
        projects = request.env['project.project'].search([
            ('name', 'ilike', project_name)],
            order=order,
        )
        values = {
            'projects': projects,
            'page_name': 'project',
            'default_url': '/my/projects',
            'searchbar_sortings': searchbar_sortings,
            'sortby': sortby,
        }
        return request.render('project.portal_my_projects', values)

    def get_year_searchbar_filters(
            self, project_date_start, project_date_create):
        year_to = fields.Datetime.from_string(fields.Datetime.now()).year
        year_from = fields.Datetime.from_string(
            project_date_start
            or project_date_create).year
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
        return searchbar_filters, year_to

    @http.route()
    def portal_my_project(self, project_id=None, access_token=None, **kw):
        res = super().portal_my_project(
            project_id=project_id, access_token=access_token, **kw)
        project = res.qcontext['project']
        if not project.allow_timesheets:
            return res
        searchbar_filters, year_to = self.get_year_searchbar_filters(
            project.date_start, project.create_date)
        domain = [
            ('project_id', '=', int(project_id)),
            ('task_id', '!=', False),
        ]
        filterby = kw.get('filterby', str(year_to))
        if filterby != 'all':
            domain.extend(searchbar_filters[filterby]['domain'])
        timesheets = request.env['account.analytic.line'].sudo().search(domain)
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
        res.qcontext['default_url'] = '/my/project/%s' % project_id
        res.qcontext['graph_data'] = json.dumps([{
            'key': _('Spent time per month (in hours)'),
            'values': [{'text': k, 'count': v} for k, v in values.items()],
        }])
        contract_lines = request.env['contract.line'].sudo().search([
            ('active', '=', True),
            ('analytic_account_id', '=', project.analytic_account_id.id),
        ])
        contract_lines = contract_lines.filtered(
            lambda line: line.state == 'in-progress')
        res.qcontext['contract_lines'] = contract_lines
        return res

    @http.route()
    def portal_my_tasks(
        self, page=1, date_begin=None, date_end=None, sortby=None,
        filterby=None, taskfilterby=None, search=None, search_in='content',
            groupby='project', **kw):
        values = self._prepare_portal_layout_values()
        searchbar_sortings = {
            'date': {'label': _('Newest'), 'order': 'create_date desc'},
            'name': {'label': _('Title'), 'order': 'name'},
            'stage': {'label': _('Stage'), 'order': 'stage_id'},
            'update': {
                'label': _('Last Stage Update'),
                'order': 'date_last_stage_update desc',
            },
        }
        searchbar_filters = {
            'all': {'label': _('All'), 'domain': []},
        }
        searchbar_task_filters = {
            'unfolded': {
                'label': _('Unfinished'),
                'domain': [('stage_id.fold', '=', False)],
            },
            'folded': {
                'label': _('Finished'),
                'domain': [('stage_id.fold', '=', True)],
            },
            'all': {'label': _('All'), 'domain': []},
        }
        searchbar_inputs = {
            'content': {
                'input': 'content',
                'label': _('Search <span class="nolabel"> (in Content)</span>'),
            },
            'message': {'input': 'message', 'label': _('Search in Messages')},
            'customer': {'input': 'customer', 'label': _('Search in Customer')},
            'stage': {'input': 'stage', 'label': _('Search in Stages')},
            'all': {'input': 'all', 'label': _('Search in All')},
        }
        searchbar_groupby = {
            'none': {'input': 'none', 'label': _('None')},
            'project': {'input': 'project', 'label': _('Project')},
        }
        projects = request.env['project.project'].search([])
        for project in projects:
            searchbar_filters.update({
                str(project.id): {
                    'label': project.name,
                    'domain': [('project_id', '=', project.id)],
                }
            })
        project_groups = request.env['project.task'].read_group(
            [('project_id', 'not in', projects.ids)],
            ['project_id'], ['project_id']
        )
        for group in project_groups:
            proj_id = group['project_id'][0] if group['project_id'] else False
            proj_name = (
                group['project_id'][1] if group['project_id'] else _('Others'))
            searchbar_filters.update({
                str(proj_id): {
                    'label': proj_name,
                    'domain': [('project_id', '=', proj_id)],
                }
            })
        if not sortby:
            sortby = 'date'
        order = searchbar_sortings[sortby]['order']
        if not filterby:
            filterby = 'all'
        domain = searchbar_filters[filterby]['domain']
        if not taskfilterby:
            taskfilterby = 'unfolded'
        domain += searchbar_task_filters[taskfilterby]['domain']
        archive_groups = self._get_archive_groups('project.task', domain)
        if date_begin and date_end:
            domain += [
                ('create_date', '>', date_begin),
                ('create_date', '<=', date_end),
            ]
        if search and search_in:
            search_domain = []
            if search_in in ('content', 'all'):
                search_domain = OR([search_domain, [
                    '|',
                    ('name', 'ilike', search),
                    ('description', 'ilike', search),
                ]])
            if search_in in ('customer', 'all'):
                search_domain = OR([search_domain, [
                    ('partner_id', 'ilike', search),
                ]])
            if search_in in ('message', 'all'):
                search_domain = OR([search_domain, [
                    ('message_ids.body', 'ilike', search),
                ]])
            if search_in in ('stage', 'all'):
                search_domain = OR([search_domain, [
                    ('stage_id', 'ilike', search),
                ]])
            domain += search_domain
        task_count = request.env['project.task'].search_count(domain)
        pager = portal_pager(
            url='/my/tasks',
            url_args={
                'date_begin': date_begin,
                'date_end': date_end,
                'sortby': sortby,
                'filterby': filterby,
                'taskfilterby': taskfilterby,
                'search_in': search_in,
                'search': search,
                'groupby': groupby,
            },
            total=task_count,
            page=page,
            step=self._items_per_page
        )
        if groupby == 'project':
            order = "project_id, %s" % order
        tasks = request.env['project.task'].search(
            domain, order=order, limit=self._items_per_page,
            offset=(page - 1) * self._items_per_page)
        request.session['my_tasks_history'] = tasks.ids[:100]
        if groupby == 'project':
            grouped_tasks = [
                request.env['project.task'].concat(*g) for k, g in groupbyelem(
                    tasks, itemgetter('project_id'))]
        else:
            grouped_tasks = [tasks]
        values.update({
            'date': date_begin,
            'date_end': date_end,
            'grouped_tasks': grouped_tasks,
            'page_name': 'task',
            'archive_groups': archive_groups,
            'default_url': '/my/tasks',
            'pager': pager,
            'searchbar_sortings': searchbar_sortings,
            'searchbar_groupby': searchbar_groupby,
            'searchbar_inputs': searchbar_inputs,
            'search_in': search_in,
            'sortby': sortby,
            'groupby': groupby,
            'searchbar_filters': OrderedDict(sorted(searchbar_filters.items())),
            'searchbar_task_filters': searchbar_task_filters,
            'filterby': filterby,
            'taskfilterby': taskfilterby,
        })
        return request.render('project.portal_my_tasks', values)

    @http.route(
        ['/my/timesheets/<int:project_id>'], type='http', auth='user',
        website=True)
    def portal_my_timesheets(self, project_id, **kw):
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
            'default_url': '/my/timesheets/%s' % project_id,
            'filterby': filterby,
            'page_name': 'timesheets',
            'project_unit_balance_display': project.unit_balance_display,
            'project_id': project_id,
            'project_name': project.name,
            'searchbar_filters': OrderedDict(
                sorted(searchbar_filters.items())),
            'timesheets': timesheets,
        })
        return request.render(
            'portal_project.portal_my_timesheets', portal_values)

    @http.route(
        ['/my/timesheets/<int:project_id>/export'], type='http', auth='user',
        website=True)
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
        if project.unit_balance_display != 'hidden':
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
            if project.unit_balance_display != 'hidden':
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
