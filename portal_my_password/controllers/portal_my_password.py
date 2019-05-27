###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.addons.portal.controllers.portal import CustomerPortal
from odoo.http import request, route
from odoo import _


class CustomerPortal(CustomerPortal):
    @route(['/my/password'], type='http', auth='user', website=True)
    def password(self, redirect=None, **post):
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        values.update({
            'error': {},
            'error_message': []})
        if post:
            error, error_message = self.password_form_validate(post)
            values.update({'error': error, 'error_message': error_message})
            values.update(post)
            if not error:
                request.env.user.write(
                    {'password': post.get('new_password')})
                return request.redirect(redirect or '/my/home')
        values.update({
            'partner': partner,
            'redirect': redirect,
            'page_name': 'my_password'})
        response = request.render('portal_my_password.my_password', values)
        response.headers['X-Frame-Options'] = 'DENY'
        return response

    def password_form_validate(self, data):
        error = dict()
        error_message = []
        new_password = data.get('new_password')
        if not new_password:
            error['new_password'] = 'missing'
            error_message.append(_('New Password is mandatory'))
        retype_new_password = data.get('retype_new_password')
        if not retype_new_password:
            error['retype_new_password'] = 'missing'
            error_message.append(_('Retype New Password is mandatory'))
        if new_password != retype_new_password:
            error['new_password'] = 'unmatch'
            error['retype_new_password'] = 'unmatch'
            error_message.append(_('Passwords do not match'))
        return error, error_message
