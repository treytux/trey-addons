# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
import re
from functools import partial
from openerp import http, _
from openerp.http import request
from openerp.addons.web.controllers import main
try:
    from openerp.tools import html2text
except ImportError:
    html2text = None
import logging
_log = logging.getLogger(__name__)

RPP = 20  # Rows per page


class Home(main.Home):
    login_redirect = '/my/home'


class MyAccount(http.Controller):
    mandatory_data_fields = ['name']
    mandatory_password_fields = ['password', 'retype_password']
    mandatory_preferences_fields = []
    editable_data_fields = ['name']
    editable_shipping_fields = [
        'name', 'vat', 'street', 'country_id', 'state_id', 'city', 'zip',
        'email', 'phone', 'mobile', 'fax', 'website']
    mandatory_shipping_fields = ['name']
    editable_billing_fields = [
        'name', 'vat', 'street', 'country_id', 'state_id', 'city', 'zip',
        'email', 'phone', 'mobile', 'fax', 'website']
    mandatory_billing_fields = ['name']
    editable_preferences_fields = ['lang', 'tz', 'notify_email']

    def _get_mandatory_data_fields(self):
        return self.mandatory_data_fields

    def _get_mandatory_password_fields(self):
        return self.mandatory_password_fields

    def _get_mandatory_preferences_fields(self):
        return self.mandatory_preferences_fields

    def _get_editable_data_fields(self):
        return self.editable_data_fields

    def _get_editable_shipping_fields(self):
        return self.editable_shipping_fields

    def _get_mandatory_shipping_fields(self):
        return self.mandatory_shipping_fields

    def _get_editable_billing_fields(self):
        return self.editable_billing_fields

    def _get_mandatory_billing_fields(self):
        return self.mandatory_billing_fields

    def _get_editable_preferences_fields(self):
        return self.editable_preferences_fields

    def _get_can_edit_address(self):
        return request.website.edit_portal_addresses

    def _is_billing_address(self, address):
        return address.type == 'invoice' or not address.parent_id

    def _get_partner_ids(self):
        env = request.env
        return list(set(
            [env.user.partner_id.root_partner_id.id] +
            env.user.partner_id.root_partner_id.child_ids.ids))

    def _get_follower_ids(self):
        env = request.env
        return [env.user.partner_id.id]

    def _get_member_ids(self):
        env = request.env
        return [env.user.id]

    def _get_partner_company(self):
        user = request.env.user
        if user.partner_id.is_company:
            return user.partner_id
        else:
            partner = user.partner_id
            if partner.parent_id:
                while partner.parent_id:
                    partner = partner.parent_id
                    if partner.is_company:
                        return partner
            else:
                return partner
        return None

    def _get_limit(self):
        return RPP

    def _get_page(self, page, max_pages):
        if page < 1:
            page = 1
        if page > max_pages:
            page = max_pages
        return page

    def _get_max_pages(self, count, rpp=RPP):
        return int(count / rpp) if count % rpp == 0 else int(count / rpp) + 1

    def _get_offset(self, page, max_pages, rpp=RPP):
        offset = 0
        if (page - 1) > 0 and page <= max_pages:
            offset = rpp * (page - 1)
        return offset

    def _html2text(self, html):
        return re.sub(r'<[^>]+>', "", html)

    def _get_mail_messages(self, model, res_id):
        env = request.env
        mail_messages = env['mail.message'].sudo().search([
            ('model', '=', model),
            ('res_id', '=', res_id),
            ('subtype_id', '=', env.ref('mail.mt_comment').id)],
            order='date desc')

        return mail_messages

    def _get_countries(self):
        env = request.env
        countries = env['res.country'].search([])
        return countries

    def _get_states(self):
        env = request.env
        states = env['res.country.state'].search([])
        return states

    @http.route([
        '/my/home', '/myaccount',
        '/mi/cuenta', '/micuenta'
    ], type='http', auth='user', website=True)
    def myaccount(self, container=None, **post):
        return request.website.render('website_myaccount.dashboard', {})

    @http.route([
        '/my/profile', '/myaccount/profile',
        '/mi/perfil', '/micuenta/perfil'
    ], type='http', auth='user', website=True)
    def profile(self, container=None, **post):
        return request.website.render('website_myaccount.profile', {
            'mandatory_data_fields': self._get_mandatory_data_fields(),
            'editable_data_fields': self._get_editable_data_fields(),
            'mandatory_preferences_fields':
                self._get_mandatory_preferences_fields(),
            'editable_shipping_fields': self._get_editable_shipping_fields(),
            'editable_billing_fields': self._get_editable_billing_fields(),
            'editable_preferences_fields':
                self._get_editable_preferences_fields(),
            'can_edit_address':
                self._get_can_edit_address()})

    @http.route([
        '/my/profile/update/data'
    ], type='json', auth='user', methods=['POST'], website=True)
    def profile_update_data(self, fields):
        env = request.env

        errors = []
        result = False
        for field in fields:
            if (field in self._get_mandatory_data_fields() and
               fields[field].strip() == ''):
                errors.append(
                    {'field': field, 'msg': 'The field is required.'})
        if not errors:
            data = {}
            if 'name' in fields:
                data['name'] = fields['name']
                result = env.user.write(data)

        return {'errors': errors, 'result': result}

    @http.route([
        '/my/profile/update/password'
    ], type='json', auth='user', methods=['POST'], website=True)
    def profile_update_password(self, fields):
        env = request.env

        errors = []
        result = False
        for field in fields:
            if (field in self._get_mandatory_password_fields() and
               fields[field].strip() == ''):
                errors.append(
                    {'field': field, 'msg': 'The field is required.'})
        if not errors:
            if (fields['new_password'] != fields['retype_new_password']):
                errors.append(
                    {'field': 'retype_new_password',
                     'msg': 'Passwords doesn\'t match.'})
        if not errors:
            data = {}
            data['password'] = fields['new_password']
            result = env.user.write(data)
            env.cr.commit()
            request.session.authenticate(
                request.session.db, env.user.login, fields['new_password'])

        return {'errors': errors, 'result': result}

    @http.route([
        '/my/profile/update/preferences'
    ], type='json', auth='user', methods=['POST'], website=True)
    def profile_update_preferences(self, fields):
        env = request.env

        errors = []
        result = False
        for field in fields:
            if (field in self._get_mandatory_data_fields() and
               fields[field].strip() == ''):
                errors.append(
                    {'field': field, 'msg': 'The field is required.'})
        if not errors:
            data = {}
            data['lang'] = fields['lang'] if 'lang' in fields else ''
            data['tz'] = fields['tz'] if 'tz' in fields else ''
            data['notify_email'] = (
                fields['notify_email'] if 'notify_email' in fields
                else 'always')
            result = env.user.write(data)

        return {'errors': errors, 'result': result}

    def _is_address_allowed(self, address_id):
        env = request.env
        user = request.env.user
        child_ids = list(set(
            user.partner_id.root_partner_id.child_ids.ids +
            [user.partner_id.root_partner_id.id]))
        addresses = env['res.partner'].sudo().search([
            ('id', '=', int(address_id)),
            ('id', 'in', child_ids)], limit=1)
        if not addresses:
            return False
        return addresses[0]

    @http.route([
        '/my/profile/address/<int:address_id>',
        '/myaccount/profile/address/<int:address_id>',
        '/mi/perfil/direccion/<int:address_id>',
        '/micuenta/perfil/direccion/<int:address_id>'],
        type='http', auth='user', website=True)
    def address(self, address_id):
        address = self._is_address_allowed(address_id)
        if not address:
            return request.website.render('website.404')
        return request.website.render('website_myaccount.address', {
            'user': request.env.user,
            'address': address,
            'countries': self._get_countries(),
            'states': self._get_states(),
            'is_billing_address': partial(self._is_billing_address),
            'editable_shipping_fields': self._get_editable_shipping_fields(),
            'mandatory_shipping_fields': self._get_mandatory_shipping_fields(),
            'editable_billing_fields': self._get_editable_billing_fields(),
            'mandatory_billing_fields': self._get_mandatory_billing_fields()})

    @http.route(['/my/profile/update/address/<int:address_id>'],
                type='json', auth='user', methods=['POST'], website=True)
    def address_update(self, address_id, fields):
        def _check_vat_code(vat, country_id=None):
            if not country_id:
                return vat
            env = request.env
            country = env['res.country'].browse(country_id)
            if not country:
                return vat
            country_code = country.code
            if not vat.startswith(country_code):
                vat = '%s%s' % (country_code, vat)
            return vat
        env = request.env
        errors = []
        result = False
        address = self._is_address_allowed(address_id)
        if not address:
            return {
                'errors': {'field': 'Error', 'msg': 'Operation not allowed.'},
                'result': result}
        for field in fields:
            if (field in self._get_mandatory_shipping_fields() and
               fields[field].strip() == ''):
                errors.append(
                    {'field': field, 'msg': 'The field is required.'})
        # TODO: Crear módulo para reutilizar validación NIF
        # Chequeo duplicado
        # Chequeo formato incorrecto
        # Añadir código país automáticamente
        # No lanzar error si pertenece al mismo partner
        vat = fields.get('vat')
        country_id = fields.get('country_id')
        country_id = int(country_id) if country_id else address.country_id
        country_id = (
            country_id if int(country_id) else
            address.company_id.country_id.id)
        if vat:
            fields['vat'] = _check_vat_code(vat, country_id)
            if fields['vat'] == address.vat:
                fields.pop('vat')
            else:
                partner = env['res.partner'].sudo().search([
                    ('vat', '=', fields['vat']),
                    ('id', 'not in', [
                        address.root_partner_id.id, address.id])], limit=1)
                if len(partner) > 0:
                    errors.append({
                        'field': 'vat',
                        'msg': _('The VAT %s already exists.') %
                        fields['vat']})
        if not errors:
            result = address.sudo().write(fields)
        return {'errors': errors, 'result': result}

    @http.route([
        '/my/message/post'
    ], type='http', auth='user', website=True)
    def message_post(self, **post):
        model = post.get('model', None)
        res_id = post.get('res_id', None)
        body_html = post.get('body_html', '').strip()

        if not model or not res_id or body_html == '':
            return

        env = request.env

        model_obj = env[model].search([('id', '=', int(res_id))])
        if model_obj:
            model_obj.with_context(mail_post_autofollow=False).message_post(
                body=body_html,
                type='email',
                subtype='mail.mt_comment',
                partner_ids=model_obj.message_follower_ids.ids)
        if not model_obj:
            return request.website.render('website.404')

        return

    # @http.route([
    #     '/my/home/get_widget_messages'
    # ], type='json', auth='user', methods=['POST'], website=True)
    # def get_widget_messages(self):
    #     env = request.env
    #     messages = env['mail.message'].sudo().search([
    #         ('partner_ids', 'in', env.user.partner_id.id),
    #         ('notified_partner_ids', 'in', env.user.partner_id.id),
    #         ('subtype_id', '=', env.ref('mail.mt_comment').id),
    #         ('to_read', '=', True)])
    #     return {'to_read': len(messages)}
