# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.
from openerp import http
from openerp.http import request
import logging
_log = logging.getLogger(__name__)
try:
    from openerp.addons.website_myaccount.controllers.main import MyAccount
except ImportError:
    MyAccount = object
    _log.error('No module named website_myaccount')


class MyAccountProjects(MyAccount):
    def _prepare_projects(self, project_id=None, limit=None):
        env = request.env
        domain = [
            '|', '|',
            ('partner_id', 'in', self._get_partner_ids()),
            ('message_follower_ids', 'in', self._get_follower_ids()),
            ('members', 'in', self._get_member_ids()),
            ('state', 'not in', ['close']),
            ('analytic_account_id.state', 'not in', ['close']),
            ('analytic_account_id.type', '=', 'contract')]
        if project_id:
            domain.append(('id', '=', project_id))
        return env['project.project'].sudo().search(domain, limit=limit)

    def _prepare_tasks(self, project_id=None, limit=None):
        env = request.env
        domain = []
        if project_id:
            domain.append(('project_id', '=', project_id))
        return env['project.task'].sudo().search(domain, limit=limit)

    @http.route([
        '/my/projects',
        '/myaccount/projects',
        '/mis/proyectos',
        '/micuenta/proyectos'
    ], type='http', auth='user', website=True)
    def projects(self, **post):
        return request.website.render(
            'website_myaccount_project.projects', {
                'projects': self._prepare_projects()})

    @http.route([
        '/my/project/<int:project_id>',
        '/myaccount/project/<int:project_id>',
        '/mi/projecto/<int:project_id>',
        '/micuenta/projecto/<int:project_id>'
    ], type='http', auth='user', website=True)
    def project(self, project_id=None, **post):
        if not project_id:
            return request.website.render('website.404')
        project = self._prepare_projects(project_id=project_id, limit=1)
        if not project:
            return request.website.render('website.404')
        return request.website.render(
            'website_myaccount_project.project', {
                'project': project,
                'tasks': self._prepare_tasks(project_id=project.id)})
