# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import http, _
from openerp.http import request
from openerp.addons.website_sale.controllers.main import website_sale


class WebsiteSale(website_sale):

    mandatory_data_fields = [
        'name', 'street', 'country_id', 'city', 'zip',
        'email', 'phone']

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
        commercial = partner.commercial_partner_id
        return request.env['res.partner'].search([
            ('id', 'child_of', commercial.ids),
            '|',
            ('type', 'in', ['delivery', 'other']),
            ('id', '=', commercial.id),
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

    @http.route(
        ['/shop/address/<model("res.partner"):partner>'],
        type='http', auth='user', website=True)
    def address(self, partner, **post):
        errors = {}
        if post:
            for field in post:
                if (field in self.mandatory_data_fields and
                   post[field].strip() == ''):
                    errors[field] = 'The field is required.'
            if not errors:
                partner.sudo().write(post)
                return request.redirect('/shop/checkout')
        values = {
            'address': partner,
            'countries': self._get_countries(),
            'states': self._get_states(),
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
                if (field in self.mandatory_data_fields and
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
            'errors': errors,
        }
        return request.website.render(
            'website_sale_addresses.new_address', values)
