# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import http, fields, _
from openerp.http import request
from functools import partial
import base64
from openerp.addons.website_myaccount.controllers.main import MyAccount


class MyAccountProjectIssues(MyAccount):
    issue_fields = ['subject', 'project',
                    'description', 'attachment', 'priority']

    def _get_issue_fields(self):
        return self.issue_fields

    def _prepare_issues(self, issue_id=None, limit=None, custom_domain=None):
        env = request.env
        projects = self._prepare_projects()
        if not projects:
            return None
        domain = [('project_id', 'in', projects.ids)]
        if custom_domain:
            domain.extend(custom_domain)
        if issue_id:
            domain.append(('id', '=', issue_id))
        issues = env['project.issue'].sudo().search(
            domain, limit=limit, order='id DESC')
        return issues

    def _get_issue_stages(self, issues=None):
        stages = []
        if issues:
            stages = list(set([s.stage_id for s in issues]))
            stages.sort(key=lambda x: x.sequence)
        return stages

    def _render_issues(self, issues, stages, stage_id, year_to, year_from,
                       scope):
        return request.website.render(
            'website_myaccount_project_issue.issues', {
                'issues': issues,
                'stages': stages,
                'stage_id': stage_id,
                'year_to': year_to,
                'year_from': year_from,
                'scope': scope})

    @http.route([
        '/my/issues',
        '/myaccount/issues',
        '/mis/incidencias',
        '/micuenta/incidencias'
    ], type='http', auth='user', website=True)
    def issues(self, **post):
        limit = 20
        issues = self._prepare_issues()
        stages = self._get_issue_stages(issues)
        year_to = fields.Datetime.from_string(fields.Datetime.now()).year
        year_from = year_to
        if issues and issues[-1].create_date:
            year_from = fields.Datetime.from_string(
                issues[-1].create_date).year
        if not post:
            return self._render_issues(
                self._prepare_issues(limit=limit), stages, 'all',
                year_to, year_from, 'latest')
        domain = []
        scope = post.get('scope', 'latest')
        stage_id = post.get('stage', None)
        stage_id = int(stage_id) if stage_id.isdigit() else stage_id
        if scope != 'latest':
            limit = None
        if scope.isdigit():
            date_from = '%s-01-01 00:00:00' % (int(scope))
            date_to = '%s-12-31 23:59:59' % (int(scope))
            domain.extend([
                ('create_date', '>=', date_from),
                ('create_date', '<=', date_to)])
        if stage_id and stage_id != 'all':
            domain.extend([('stage_id', '=', stage_id)])
        return self._render_issues(
            self._prepare_issues(limit=limit, custom_domain=domain), stages,
            stage_id, year_to, year_from, scope)

    @http.route([
        '/my/issue/<int:issue_id>',
        '/myaccount/issue/<int:issue_id>',
        '/mi/incidencia/<int:issue_id>',
        '/micuenta/incidencia/<int:issue_id>'
    ], type='http', auth='user', website=True)
    def issue(self, issue_id=None, **post):
        projects = self._prepare_projects()
        if not projects or not issue_id:
            return request.website.render('website.404')
        issue = self._prepare_issues(issue_id=issue_id)
        if not issue:
            return request.website.render('website.404')
        messages_ids = issue.message_ids
        params = request.params
        if params.get('mode', '') == 'send':
            issue.with_context(mail_post_autofollow=False).message_post(
                body=params.get('body_html', ''),
                type='email',
                subtype='mail.mt_comment',
                partner_ids=issue.message_follower_ids.ids)
        return request.website.render(
            'website_myaccount_project_issue.issue', {
                'issue': issue,
                'messages': messages_ids,
                'html2text': partial(self._html2text)})

    @http.route(
        ['/my/issue/new', '/my/new-issue'],
        type='http', auth='user', website=True)
    def new_issue(self, **post):
        params = request.params
        env = request.env
        errors = []
        domain = [
            '|',
            ('partner_id', 'in', self._get_partner_ids()),
            ('message_follower_ids', 'in', self._get_follower_ids()),
            ('state', 'not in', ['close']),
            ('analytic_account_id.state', 'not in', ['close']),
            ('analytic_account_id.type', '=', 'contract')]
        project = env['project.project'].sudo().search(domain, limit=20)
        issues_obj = env['project.issue']
        priority_types = issues_obj._columns['priority'].selection
        if params.get('mode', '') == 'create':
            if params.get('name', '') in ['', ' ']:
                errors.append(_('Error in subject value\n'))
            if params.get('description', '') in ['', ' ']:
                errors.append(_('Error in description value\n'))
            if errors:
                return request.website.render(
                    'website_myaccount_project_issue.new_issue', {
                        'user': request.env.user,
                        'errors': errors,
                        'projects': project,
                        'priorities': priority_types})
            issue = env['project.issue'].sudo().create({
                'name': params.get('name'),
                'priority': params.get('priority'),
                'partner_id': request.env.user.partner_id.id,
                'description': params.get('description'),
                'project_id': params.get('project'),
                'progress': 0.0})
            mail_message = env['mail.message'].sudo().create({
                'model': 'project.issue',
                'res_id': issue.id,
                'author_id': request.env.user.partner_id.id,
                'type': 'notification',
                'subject': params.get('name'),
                'body': params.get('description')})
            attachment = params.get('attachment', False)
            if attachment:
                attachment_file = attachment.stream
                attachment_values = {
                    'res_model': 'mail.message',
                    'res_id': mail_message.id,
                    'datas_fname': attachment.filename,
                    'datas': base64.encodestring(attachment_file.read()),
                    'name': attachment.filename
                }
                attachment_obj = env['ir.attachment'].sudo().create(
                    attachment_values)
                mail_message.update({'attachment_ids': [attachment_obj.id]})
                attachment_obj.sudo().write({'res_id': mail_message.id})
            return request.redirect('/my/issues')
        return request.website.render(
            'website_myaccount_project_issue.new_issue', {
                'user': request.env.user,
                'projects': project,
                'priorities': priority_types,
                'issue': self._get_issue_fields()})

    @http.route(
        ['/my/message-issue/post'],
        type='http', auth='user', website=True)
    def message_post(self, **post):
        params = request.params
        attachment = params.get('attachment', False)
        res_id = params.get('res_id', False)
        if not params.get('body_html') and not attachment:
            return request.redirect(''.join(['/my/issue/', res_id]))
        env = request.env
        mail_message = env['mail.message'].sudo().create({
            'model': str(params.get('model')),
            'res_id': int(params.get('res_id')),
            'author_id': request.env.user.partner_id.id,
            'type': 'notification',
            'subject': params.get('name'),
            'body': params.get('body_html')})
        if attachment:
            attachment_file = attachment.stream
            attachment_values = {
                'res_model': 'mail.message',
                'res_id': mail_message.id,
                'datas_fname': attachment.filename,
                'datas': base64.encodestring(attachment_file.read()),
                'name': attachment.filename
            }
            attachment_obj = env['ir.attachment'].sudo().create(
                attachment_values)
            mail_message.update({'attachment_ids': [attachment_obj.id]})
            attachment_obj.sudo().write({'res_id': mail_message.id})
        return request.redirect(''.join(['/my/issue/', res_id]))
