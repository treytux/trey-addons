# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.

from openerp import http
from openerp.http import request


class MyAccount(http.Controller):

    def get_partner_company(self):
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

    @http.route([
        '/myaccount/claims',
        '/micuenta/reclamaciones'
    ], type='http', auth='user', website=True)
    def claims(self, **post):
        env = request.env
        partner = self.get_partner_company()
        if partner:
            claims = env['crm.claim'].sudo().search(
                [('partner_id', '=', partner.id)])
        else:
            claims = []
        return request.website.render(
            'website_myaccount_claim.claims',
            {'claims': claims})

    @http.route([
        '/myaccount/claim/<int:claim_id>',
        '/micuenta/reclamacion/<int:claim_id>'
    ], type='http', auth='user', website=True)
    def claim(self, claim_id, **post):
        env = request.env
        claim = env['crm.claim'].sudo().browse(int(claim_id))
        if not claim:
            return self.servers(**post)
        return request.website.render('website_myaccount_claim.claim',
                                      {'claim': claim})

    @http.route([
        '/myaccount/claim/new',
        '/micuenta/reclamacion/nueva'
    ], type='http', auth='user', website=True)
    def claimnew(self, **kwargs):
        env = request.env
        _REQUIRED = ['name', 'description']  # field required

        partner = self.get_partner_company()
        if not partner:
            return {'error': True,
                    'msm': u'Debe iniciar sesion para acceder a este area'}

        values = {}
        claim_categories = env['crm.case.categ'].sudo().search(
            [('object_id.model', '=', 'crm.claim')], order='name asc')

        values['claim_categories'] = claim_categories
        values['categ_id'] = []
        if len(kwargs) > 0:
            for field_name, field_value in kwargs.items():
                values[field_name] = field_value

            if "name" not in kwargs and values.get("name"):
                values["name"] = values.get("name")
            error = set(field for field in _REQUIRED if not values.get(field))
            if error:
                values = dict(values, error=error, kwargs=kwargs.items())
                return request.website.render(kwargs.get(
                    "view_from", "website_myaccount_claim.claim_form"), values)

            values['partner_id'] = partner.id
            values['user_id'] = ''
            values['partner_phone'] = partner.phone
            values['email_from'] = partner.email

            claim = env['crm.claim'].sudo().create(values)
            return request.website.render(
                'website_myaccount_claim.claim', {'claim': claim})
        else:
            return request.website.render(
                "website_myaccount_claim.claim_form", values)
