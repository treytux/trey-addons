# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import http
from openerp.http import request
import openerp.addons.website_sale.controllers.main as main


class WebsiteSale(main.website_sale):

    def get_partner_company(self):
        user = request.env.user
        if user.partner_id.is_company:
            return user.partner_id
        else:
            partner = user.partner_id
            while partner.parent_id:
                partner = partner.parent_id
                if partner.is_company:
                    return partner
        return None

    @http.route(['/shop/confirmation'], type='http',
                auth="public", website=True)
    def payment_confirmation(self, **post):
        res = super(WebsiteSale, self).payment_confirmation()
        if res.qcontext['order']:
            order = res.qcontext['order']
            env = request.env

            if request.uid != request.website.user_id.id:
                partner = self.get_partner_company()
                if partner and partner.id == order.partner_id.id:
                    return request.website.render(
                        "website_sale.confirmation", {'order': order})
            else:
                survey_group_id = env['res.groups'].sudo().search([
                    ('name', 'ilike', '%Encuesta / U%')])
                if survey_group_id:
                    label = 'in_group_' + str(survey_group_id.id)
                else:
                    label = ''
                value = {
                    'name': order.partner_id.name,
                    'login': order.partner_id.email,
                    'partner_id': order.partner_id.id,
                    'in_group_2': True,
                    'in_group_11': False,
                    'sel_groups_24_25_26': 0,
                    'sel_groups_5': 0,
                    'sel_groups_22_23': 0,
                    'sel_groups_21': 0,
                    'sel_groups_3_4': 0,
                    label: True,
                    'share': True,
                }
                request.env['res.users'].sudo().create(value)
                return request.website.render(
                    "website_sale.confirmation", {'order': order})
