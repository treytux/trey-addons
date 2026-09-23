###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import http
from odoo.http import request


class PortalProjectTaskWorkorders(http.Controller):

    @http.route(
        '/my/workorder-list', type='http', auth='user',
        csrf=False, website=True)
    def get_project_task_workorders_list(self, **kw):
        workorders_project = request.env.company.workorders_project
        tasks = request.env['project.task'].search([
            ('project_id', '=', workorders_project.id),
            ('is_closed', '=', False),
        ])
        values = {
            'tasks': tasks,
            'page_name': 'workorders',
            'default_url': '/my/workorder-list',
        }
        return request.render(
            'portal_project_task_workorder.portal_workorder', values)

    @http.route(
        '/my/workorder-form', type='http', auth='user',
        csrf=False, website=True)
    def redirect_project_task_workorders_list(self, **kw):
        centers = request.env['stock.location'].search([
            ('is_center', '=', True),
        ])
        values = {
            'centers': centers,
            'page_name': 'workorder_form',
            'default_url': '/my/workorder-form',
        }
        return request.render(
            'portal_project_task_workorder.portal_workorder_form', values)

    @http.route(
        '/my/create_workorder_form', type='http', auth='user', csrf=False)
    def create_project_task_workorder_from_form(self, **kw):
        workorder_project = request.env.company.workorders_project
        if not workorder_project:
            return request.redirect('/shop')
        task = request.env['project.task'].create({
            'name': request.params['name'],
            'description': request.params['description'],
            'project_id': workorder_project.id,
            'center': int(request.params['center_locations']),
            'workorder_create_user': request.env.user.id,
            'portal_created': True,
        })
        followers = workorder_project.message_follower_ids
        mail_template = request.env.ref(
            'portal_project_task_workorder.email_template_create_workorder')
        user_email = request.env.user.email
        email_list = {
            'email_to': ', '.join(followers.mapped('email') + [user_email]),
        }
        mail_template.send_mail(
            task.id, force_send=True, email_values=email_list)
        return request.redirect('/my/workorder-list')
