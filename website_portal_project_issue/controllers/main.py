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


class PortalProjectIssueWebsiteAccount(WebsiteAccount):
    def _prepare_issues(self, limit=None, **kw):
        projects = request.env['project.project'].search(
            [('state', 'in', ['open', 'pending'])])
        issues = request.env['project.issue'].search(
            [('project_id', 'in', projects.ids)], limit=limit, order='id DESC')
        return issues

    @http.route(
        ['/my/issues'], type='http', auth="user", website=True)
    def project_issues(self, **kw):
        issues = {'issues': self._prepare_issues()}
        return request.website.render(
            'website_portal_project_issue.issues_only', issues)

    @http.route(
        ['/my/issue/<int:issue_id>'],
        type='http', auth="user", website=True, methods=['GET', 'POST'])
    def issues_followup(self, issue_id=None, **post):
        domain = [('id', '=', int(issue_id))]
        issue = request.env['project.issue'].search(domain)
        mail_messages = request.env['mail.message'].search([
            ('model', '=', 'project.issue'),
            ('res_id', '=', issue.id),
            ('type', 'in', ['email'])],
            order='date desc')
        params = request.params
        if params.get('mode', '') == 'send':
                issue.with_context(mail_post_autofollow=False).message_post(
                    body=params.get('body_html', ''),
                    type='email',
                    partner_ids=issue.message_follower_ids.ids)
        if not issue:
            return request.website.render("website.404")
        return request.website.render(
            "website_portal_project_issue.issues_followup",
            {'issue': issue,
             'mail_messages': mail_messages})

    @http.route(['/my/home'], type='http', auth="user", website=True)
    def account(self, **kw):
        """ Add projects documents to main account page """
        response = super(PortalProjectIssueWebsiteAccount, self).account(**kw)
        if not request.env.user.partner_id.customer:
            return response
        issues = self._prepare_issues(20)
        response.qcontext.update({
            'issues': issues,
        })
        return response
