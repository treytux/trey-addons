# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.

from openerp import http
from openerp.http import request
import logging

_log = logging.getLogger(__name__)


class WebsitePortfolio(http.Controller):
    @http.route([
        '/portfolio',
        '/portfolio/page/<int:page>',
    ], type='http', auth="public", website=True)
    def portfolio(self, page=1, **post):
        env = request.env
        projects = env['portfolio.project'].sudo().search([])
        tags = env['portfolio.tag'].sudo().search([])

        return request.website.render('website_portfolio.portfolio', {
            'projects': projects,
            'tags': tags})

    @http.route([
        '/portfolio/project/<model("portfolio.project"):project>',
    ], type='http', auth="public", website=True)
    def project(self, project, **post):
        return request.website.render('website_portfolio.single_project', {
            'project': project})
