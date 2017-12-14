# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.
import json
from openerp import http, fields
from openerp.http import request
from collections import OrderedDict
from openerp.tools.translate import _
import logging
_log = logging.getLogger(__name__)
try:
    from openerp.addons.website_myaccount.controllers.main import MyAccount
except ImportError:
    MyAccount = object
    _log.error('No module named website_myaccount')


class MyAccountContract(MyAccount):
    def _prepare_contracts(self, contract_id=None, limit=None):
        env = request.env
        domain = [
            '|',
            ('partner_id', 'in', self._get_partner_ids()),
            ('message_follower_ids', 'in', self._get_follower_ids()),
            ('state', 'in', ['open', 'pending'])]
        if contract_id:
            domain.append(('id', '=', contract_id))
        contracts = env['account.analytic.account'].sudo().search(
            domain, limit=limit)
        return contracts

    @http.route([
        '/my/contracts',
        '/myaccount/contracts',
        '/mis/contratos',
        '/micuenta/contratos'
    ], type='http', auth='user', website=True)
    def contracts(self):
        contracts = {'contracts': self._prepare_contracts()}
        return request.website.render(
            'website_myaccount_contract.contracts', contracts)

    @http.route([
        '/my/contract/<int:contract_id>',
        '/myaccount/contract/<int:contract_id>',
        '/mi/contrato/<int:contract_id>',
        '/micuenta/contrato/<int:contract_id>'
    ], type='http', auth='user', website=True)
    def contract(self, contract_id=None, **post):
        timesheets = None
        graph_data_dict = {}
        scope = None
        scope = (
            post.get('scope') if post and post.get('scope') else scope)
        year = None
        year = int(post.get('year')) if post and post.get('year') else year
        year_to = fields.Datetime.from_string(
            fields.Datetime.now()).year
        year_from = year_to

        contract = self._prepare_contracts(
            contract_id=contract_id, limit=1)

        if not contract:
            return request.website.render('website.404')

        if contract.date_start:
            year_from = fields.Datetime.from_string(
                contract.date_start).year

        if contract.use_timesheets:
            domain = [
                ('account_id', '=', contract_id)
            ]
            if scope != 'all':
                date_from = fields.Datetime.from_string(
                    '%s-01-01 00:00:00' % (year if year else year_to))
                date_to = fields.Datetime.from_string(
                    '%s-12-31 23:59:59' % (year if year else year_to))
                domain.extend(
                    [('date', '>=', date_from), ('date', '<=', date_to)])
            timesheets = request.env['hr.analytic.timesheet'].sudo().search(
                domain, order='id DESC')

            if timesheets:
                if scope != 'all':
                    for m in range(12):
                        key = '%s / %s' % (
                            year if year else year_to,
                            str(m + 1).zfill(2))
                        graph_data_dict[key] = 0
                    for t in timesheets:
                        key = '%s / %s' % (
                            fields.Datetime.from_string(t.date).year,
                            str(fields.Datetime.from_string(
                                t.date).month).zfill(2))
                        graph_data_dict[key] += t.unit_amount
                else:
                    for y in range(year_to - year_from + 1):
                        key = '%s' % (
                            year_from + y)
                        graph_data_dict[key] = 0
                    for t in timesheets:
                        key = '%s' % (
                            fields.Datetime.from_string(t.date).year)
                        graph_data_dict[key] += t.unit_amount
                graph_data_dict = OrderedDict(sorted(graph_data_dict.items()))
        graph_data = [{
            'key': _('Spent time per month (in hours)'),
            'values': [{
                'text': item,
                'count': graph_data_dict[item]
            } for item in graph_data_dict] if graph_data_dict else []}]

        domain = [
            ('analytic_account_id', '=', contract_id)
        ]
        project = request.env['project.project'].sudo().search(domain)
        issues = None
        if project:
            domain = [
                ('project_id', '=', project.id)
            ]
            issues = request.env['project.issue'].sudo().search(domain)

        return request.website.render(
            'website_myaccount_contract.contract', {
                'contract': contract,
                'project': project,
                'issues': issues,
                'timesheets': timesheets,
                'year_from': year_from,
                'year_to': year_to,
                'year': year if year else year_to,
                'scope': scope,
                'graph_data': json.dumps(graph_data),
            })
