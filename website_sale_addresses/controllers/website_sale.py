# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import http, _
from openerp.http import request
from openerp import tools
from openerp.addons.website_sale.controllers.main import website_sale


class WebsiteSale(website_sale):
    mandatory_billing_fields = [
        'city',
        'country_id',
        'name',
        'state_id',
        'street',
        'zip',
    ]
    optional_billing_fields = [
        'email',
        'phone',
        'street2',
        'vat',
        'vat_subjected',
    ]
    mandatory_shipping_fields = [
        'city',
        'country_id',
        'name',
        'state_id',
        'street',
        'zip',
    ]
    optional_shipping_fields = [
        'email',
        'phone',
        'street2',
    ]

    def _get_countries(self):
        env = request.env
        countries = env['res.country'].search([])
        return countries

    def _get_states(self):
        env = request.env
        states = env['res.country.state'].search([])
        return states

    def _get_shippings(self):
        user = request.env['res.users'].browse(request.uid)
        partner = user.sudo().partner_id
        return request.env['res.partner'].search([
            ('id', 'child_of', partner.ids),
            '|',
            ('type', 'in', ['contact', 'delivery', 'other']),
            ('id', '=', partner.id),
        ])

    @http.route(auth='user')
    def checkout(self, **post):
        result = super(WebsiteSale, self).checkout(**post)
        shipping = post.get('shipping')
        order = request.website.sale_get_order(force_create=1)
        if shipping:
            order.partner_shipping_id = request.env['res.partner'].browse(
                shipping)
        values = self.checkout_values(post)
        error = super(WebsiteSale, self).checkout_form_validate(
            values['checkout'])
        for field_name in self._get_mandatory_shipping_fields():
            if not order.partner_shipping_id[field_name]:
                error[field_name] = 'missing'
        result.qcontext['order'] = order
        result.qcontext['shippings'] = self._get_shippings()
        result.qcontext['error'] = error
        return result

    @http.route(auth='user')
    def confirm_order(self, **post):
        result = super(WebsiteSale, self).confirm_order(**post)
        if 'error' in result.qcontext and result.qcontext['error']:
            order = request.website.sale_get_order(force_create=1)
            result.qcontext['order'] = order
            result.qcontext['shippings'] = self._get_shippings()
        return result

    @http.route(
        ['/shop/shipping_address/<model("res.partner"):partner>'],
        type='http', auth='user', website=True)
    def shipping_address(self, partner, **post):
        order = request.website.sale_get_order(force_create=1)
        if partner:
            order.partner_shipping_id = partner
        return request.redirect('/shop/checkout')

    def check_vat_country_code(self, address):
        if (
            'vat' in address and
            address['vat'] != '' and
            'country_id' in address and
                address['country_id'] != ''):
            country = request.env['res.country'].browse(
                int(address['country_id']))
            if country and address['vat'][:2] != country.code:
                address['vat'] = country.code + address['vat']
        return address

    def address_validate(self, address, address_type):
        errors = {}
        mandatory_fields = (
            address_type == 'invoicing' and
            self._get_mandatory_billing_fields() or
            self._get_mandatory_shipping_fields())
        for field in mandatory_fields:
            value = address.get(field, False)
            if not value or value == '':
                errors[field] = _('The field is required.')
        if (
            'email' in address and
            address['email'] != '' and
                not tools.single_email_re.match(address['email'])):
            errors['email'] = _('Wrong email format.')
        res_partner = request.registry['res.partner']
        if (
            'vat' in address and
            address['vat'] != '' and
                hasattr(res_partner, 'check_vat')):
            address = self.check_vat_country_code(address)
            if request.website.company_id.vat_check_vies:
                check_func = res_partner.vies_vat_check
            else:
                check_func = res_partner.simple_vat_check
            vat_country, vat_number = res_partner._split_vat(address['vat'])
            if not check_func(
                request.cr, request.uid, vat_country, vat_number,
                    request.context):
                errors['vat'] = _('Wrong VAT number.')
        return errors

    @http.route(
        ['/shop/address/<string:address_type>/<model("res.partner"):address>'],
        type='http', auth='user', website=True)
    def address(self, address_type, address, **post):
        errors = {}
        if post:
            errors = self.address_validate(post, address_type)
            if not errors:
                address.sudo().write(post)
                return request.redirect('/shop/checkout')
        values = {
            'address_type': address_type,
            'address': address,
            'countries': self._get_countries(),
            'states': self._get_states(),
            'mandatory_billing_fields': self._get_mandatory_billing_fields(),
            'mandatory_shipping_fields': self._get_mandatory_shipping_fields(),
            'errors': errors,
        }
        return request.website.render('website_sale_addresses.address', values)

    @http.route(
        ['/shop/address/new/<model("res.partner"):partner>'],
        type='http', auth='user', website=True)
    def new_address(self, partner, **post):
        errors = {}
        if post:
            for field in post:
                if (field in self._get_mandatory_shipping_fields() and
                   post[field].strip() == ''):
                    errors[field] = _('The field is required.')
                if not errors:
                    post['parent_id'] = partner.commercial_partner_id.id
                    post['type'] = 'delivery'
                    request.env['res.partner'].sudo().create(post)
                    return request.redirect('/shop/checkout')
        values = {
            'address': partner,
            'countries': self._get_countries(),
            'states': self._get_states(),
            'mandatory_shipping_fields': self._get_mandatory_shipping_fields(),
            'errors': errors,
        }
        return request.website.render(
            'website_sale_addresses.new_address', values)
