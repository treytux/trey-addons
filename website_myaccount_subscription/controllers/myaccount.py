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
        '/myaccount/subscriptions',
        '/micuenta/suscripciones'
    ], type='http', auth='user', website=True)
    def subscriptions(self, container=None, **post):
        env = request.env
        partner = self.get_partner_company()
        if partner:
            subscriptions = env['learning.subscription'].search(
                [('partner_id', '=', partner.id)], order='id desc')
        else:
            subscriptions = []
        return request.website.render(
            'website_myaccount_subscription.subscriptions',
            {'subscriptions': subscriptions})

    @http.route([
        '/myaccount/certificates',
        '/micuenta/certificados'
    ], type='http', auth='user', website=True)
    def certificates(self, container=None, **post):
        env = request.env
        partner = self.get_partner_company()
        if partner:
            certificates = env['learning.subscription'].search(
                [('partner_id', '=', partner.id)], order='id desc')
        else:
            certificates = []

        return request.website.render(
            'website_myaccount_subscription.certificates',
            {'certificates': certificates})

    @http.route([
        '/myaccount/subscriptions/download/certificate/<int:subscription_id>',
        '/micuenta/suscripciones/descargar/certificado/<int:subscription_id>'
    ], type='http', auth='user', website=True)
    def diploma_download(self, subscription_id, **post):
        env = request.env
        subscription = env['learning.subscription'].browse(subscription_id)
        if subscription.exists() and \
                subscription.partner_id.id == env.user.partner_id.id \
                and subscription.approved:
            pdf = env['report'].get_pdf(
                subscription, 'audat_elearning.certificate_audat_learning')

            pdfhttpheaders = [
                ('Content-Type', 'application/pdf'),
                ('Content-Length', len(pdf))]
            return request.make_response(pdf, headers=pdfhttpheaders)
        return ''  # The Silence is Golden

    # @http.route([
    #     '/myaccount/exams',
    #     '/micuenta/examenes'
    # ], type='http', auth='user', website=True)
    # def exams(self, container=None, **post):
    #     env = request.env
    #     partner = self.get_partner_company()
    #     if partner:
    #         exams = env['survey.user_input'].search(
    #             [('partner_id', '=', partner.id),
    #             ('state', '=', 'done')], order='id desc')
    #     else:
    #         exams = []
    #     return request.website.render(
    #         'website_myaccount_subscription.exams',
    #         {'exams': exams})

    @http.route([
        '/myaccount/exams/<int:subscription_id>',
        '/micuenta/examenes/<int:subscription_id>'
    ], type='http', auth='user', website=True)
    def exam(self, subscription_id, **post):
        env = request.env
        subscription = env['learning.subscription'].browse(subscription_id)
        if subscription.exists():

            return request.website.render(
                'website_myaccount_subscription.exams',
                {'exams': subscription.user_input_ids})
