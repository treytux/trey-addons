# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import http
from openerp.http import request
try:
    from openerp.addons.website_portal.controllers.main import WebsiteAccount
except ImportError:
    WebsiteAccount = object


class PortalProjectWebsiteAccount(WebsiteAccount):
    def _prepare_projects(self, limit=None, **kw):
        # Privacidad / Visibilidad > Proyecto relacionado del cliente:
        # visible a través del portal
        projects = request.env['project.project'].search(
            [('state', 'in', ['open', 'pending'])], limit=limit)
        return projects

    @http.route(
        ['/my/projects'], type='http', auth="user", website=True)
    def projects(self, **kw):
        projects = {'projects': self._prepare_projects()}
        return request.website.render(
            'website_portal_project.projects_only', projects)

    @http.route(
        ['/my/project/<int:project_id>'],
        type='http', auth="user", website=True)
    def projects_followup(self, project_id=None):
        domain = [('id', '=', int(project_id))]
        project = request.env['project.project'].search(domain)
        if not project:
            return request.website.render("website.404")
        return request.website.render(
            "website_portal_project.projects_followup",
            {'project': project})

    @http.route(['/my/home'], type='http', auth="user", website=True)
    def account(self, **kw):
        """ Add projects documents to main account page """
        response = super(PortalProjectWebsiteAccount, self).account(**kw)
        if not request.env.user.partner_id.customer:
            return response
        projects = self._prepare_projects(20)
        response.qcontext.update({
            'projects': projects,
        })
        return response
