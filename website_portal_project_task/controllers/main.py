# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import http
from openerp.http import request
import logging
try:
    from openerp.addons.website_portal.controllers.main import WebsiteAccount
except ImportError:
    WebsiteAccount = object
    _log = logging.getLogger(__name__)
    _log.error('No module website_portal')

_log = logging.getLogger(__name__)


class PortalProjectTaskWebsiteAccount(WebsiteAccount):
    def _prepare_tasks(self, limit=None, **kw):
        projects = request.env['project.project'].search(
            [('state', 'in', ['open', 'pending'])])
        tasks = request.env['project.task'].search(
            [('project_id', 'in', projects.ids)], limit=limit, order='id DESC')
        return tasks

    @http.route(
        ['/my/tasks'], type='http', auth="user", website=True)
    def project_tasks(self, **kw):
        tasks = {'tasks': self._prepare_tasks()}
        return request.website.render(
            'website_portal_project_task.tasks_only', tasks)

    @http.route(
        ['/my/task/<int:task_id>'],
        type='http', auth="user", website=True, methods=['GET', 'POST'])
    def tasks_followup(self, task_id=None, **post):
        domain = [('id', '=', int(task_id))]
        task = request.env['project.task'].search(domain)
        mail_messages = request.env['mail.message'].search([
            ('model', '=', 'project.task'),
            ('res_id', '=', task.id),
            ('type', 'in', ['email'])],
            order='date desc')

        params = request.params
        if params.get('mode', '') == 'send':
            task.with_context(mail_post_autofollow=False).message_post(
                body=params.get('body_html', ''),
                type='email',
                partner_ids=task.message_follower_ids.ids)
        if not task:
            return request.website.render("website.404")
        return request.website.render(
            "website_portal_project_task.tasks_followup",
            {'task': task,
             'mail_messages': mail_messages})

    @http.route(['/my/home'], type='http', auth="user", website=True)
    def account(self, **kw):
        """ Add projects documents to main account page """
        response = super(PortalProjectTaskWebsiteAccount, self).account(**kw)
        if not request.env.user.partner_id.customer:
            return response
        tasks = self._prepare_tasks(20)
        response.qcontext.update({
            'tasks': tasks,
        })
        return response
