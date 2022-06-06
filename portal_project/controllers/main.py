###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import json
from collections import OrderedDict

from odoo import _, fields, http
from odoo.addons.portal.controllers.portal import CustomerPortal
from odoo.http import request


class CustomerPortal(CustomerPortal):
    @http.route()
    def portal_my_project(
            self, project_id=None, access_token=None, **kw):
        res = super().portal_my_project(
            project_id=project_id, access_token=access_token, **kw)
        project = res.qcontext['project']
        if not project.allow_timesheets:
            return res
        year_to = fields.Datetime.from_string(fields.Datetime.now()).year
        year_from = fields.Datetime.from_string(
            project.date_start
            and project.date_start
            or project.create_date).year
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
        domain = [
            ('project_id', '=', int(project_id)),
            ('task_id', '!=', False),
        ]
        filterby = kw.get('filterby', str(year_to))
        if filterby != 'all':
            domain.extend(searchbar_filters[filterby]['domain'])
        timesheets = request.env['account.analytic.line'].sudo().search(domain)
        values = {}
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
            lambda l: l.state == 'in-progress')
        res.qcontext['contract_lines'] = contract_lines
        return res

    @http.route(
        ['/my/projects/search'], type='http', auth="public", website=True)
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
        values = {}
        values.update({
            'projects': projects,
            'page_name': 'project',
            'default_url': '/my/projects',
            'searchbar_sortings': searchbar_sortings,
            'sortby': sortby,
        })
        return request.render("project.portal_my_projects", values)
