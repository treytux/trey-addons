###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, http
from odoo.addons.portal.controllers.portal import CustomerPortal
from odoo.exceptions import AccessError, MissingError
from odoo.http import request


class PortalCreateTask(CustomerPortal):

    @http.route(['/my/projects/<int:project_id>/task/new'], type='http',
                auth='user', website=True, methods=['GET', 'POST'], csrf=True)
    def portal_task_new(self, project_id, **post):
        try:
            self._document_check_access('project.project', project_id)
        except (AccessError, MissingError):
            return request.redirect('/my/projects')
        project = request.env['project.project'].sudo().browse(project_id).exists()
        if not project:
            return request.not_found()
        if request.httprequest.method == 'POST':
            name = (post.get('name') or '').strip()
            description = post.get('description') or ''
            if not name:
                values = {'project': project, 'error': _('Name is required.'),
                          'default_name': name, 'default_description': description}
                return request.render(
                    'portal_create_task.portal_create_task_form', values
                )
            request.env['project.task'].sudo().create({
                'name': name,
                'project_id': project.id,
                'description': description,
                'partner_id': request.env.user.partner_id.id,
                'user_ids': False,
            })
            return request.redirect(f"/my/projects/{project.id}")
        values = {'project': project}
        return request.render('portal_create_task.portal_create_task_form', values)
