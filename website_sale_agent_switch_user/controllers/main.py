###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import psycopg2
from odoo import exceptions, http
from odoo.addons.web.controllers.main import login_and_redirect
from odoo.http import request


class WebsiteSaleAgentSwitchUser(http.Controller):
    def get_partners_related_to_agent(self, partner_id):
        return request.env['res.partner'].sudo().search([
            ('agents', 'in', partner_id),
            ('user_ids', '!=', False),
        ], order='display_name asc').ids

    @http.route(['/change_user'], type='http', auth='user', website=True)
    def list_partners_related_to_agent(self):
        partner_id = request.env.user.sudo().partner_id.id
        partners = self.get_partners_related_to_agent(partner_id)
        users = request.env['res.users'].sudo().search([
            ('partner_id', 'in', partners),
        ], order='display_name asc')
        values = {
            'users': users,
        }
        return request.render(
            'website_sale_agent_switch_user.change_user', values)

    @http.route(
        ['/change_user/accept'], type='http', methods=['POST'], auth='user',
        website=True)
    def agent_change_user(self, **post):
        try:
            request.env['res.users'].check(
                http.request.session.db, request.env.user.id, post.get(
                    'password'))
        except exceptions.AccessDenied:
            return request.render(
                'website_sale_agent_switch_user.agent_password_error')
        partners = self.get_partners_related_to_agent(
            request.env.user.sudo().partner_id.id)
        users = request.env['res.users'].sudo().search([
            ('partner_id', 'in', partners),
        ]).ids
        if int(post.get('select_user')) not in users:
            return request.render(
                'website_sale_agent_switch_user.user_not_allowed')
        try:
            user_id = int(post.get('select_user'))
            user = request.env['res.users'].sudo().browse(user_id)
            request.env.cr.execute('''
                SELECT password FROM res_users WHERE id=%s''',
                                   (user.id,))
            password = request.env.cr.fetchone()
            credentials = (request.env.cr.dbname, user.login, str(password))
            return login_and_redirect(*credentials, redirect_url='/my')
        except psycopg2.Error:
            return request.render(
                'website_sale_agent_switch_user.redirect_error_unknown')
