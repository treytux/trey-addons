###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import base64

from odoo import fields, http
from odoo.addons.portal.controllers.portal import CustomerPortal
from odoo.http import request


class CustomerPortal(CustomerPortal):
    def _get_agreements_domain(self):
        partner_id = request.env.user.sudo().partner_id
        return [('partner_id', '=', partner_id.commercial_partner_id.id)]

    def _get_domain_agreements_unaccepted(self):
        partner_id = request.env.user.sudo().partner_id
        return [
            ('partner_id', '=', partner_id.commercial_partner_id.id),
            ('state', '=', 'unaccepted'),
        ]

    def _prepare_portal_layout_values(self):
        values = super()._prepare_portal_layout_values()
        website = request.env['website'].get_current_website()
        agreements = request.env['agreement.acceptance']
        agreements_count = agreements.search_count(
            self._get_agreements_domain())
        agreements_unaccepted = request.env['agreement.acceptance'].search(
            self._get_domain_agreements_unaccepted(),
            order='create_date desc, id desc',
            limit=website.limit_agreements)
        values.update({
            'agreements_count': agreements_count,
            'unaccepted': agreements_unaccepted,
        })
        return values

    @http.route(['/my/agreements'], type='http', auth='user', website=True)
    def portal_my_agreements(self):
        values = {}
        partner_id = request.env.user.sudo().partner_id
        commercial_partner_id = partner_id.commercial_partner_id
        agreements_unaccepted = commercial_partner_id.agreements_unaccepted
        agreements = request.env['agreement.acceptance'].search(
            self._get_agreements_domain())
        values.update({
            'page_name': 'agreements',
            'agreements': agreements,
            'agreements_unaccepted': agreements_unaccepted,
        })
        return request.render(
            'portal_agreement_acceptance.portal_my_agreements', values)

    @http.route(
        ['/my/agreements/accept/all'], type='http', auth='user',
        website=True)
    def portal_my_agreements_accept_all(self):
        partner_id = request.env.user.sudo().partner_id
        agreements = request.env['agreement.acceptance'].search([
            ('state', '=', 'unaccepted'),
            ('partner_id', '=', partner_id.commercial_partner_id.id)])
        for agreement_id in agreements:
            agreement_id.state = 'accepted'
            agreement_id.acceptance_date = fields.Date.today()
            agreement_id.acceptance_partner_id = partner_id
        return request.redirect('/my/agreements')

    @http.route(
        ['/my/agreements/accept/<int:agreement_id>'], type='http', auth='user',
        website=True)
    def portal_my_agreements_accept(self, agreement_id):
        partner_id = request.env.user.sudo().partner_id
        agreements = request.env['agreement.acceptance'].search([
            ('id', '=', agreement_id),
            ('partner_id', '=', partner_id.commercial_partner_id.id)])
        if agreements:
            agreements[0].state = 'accepted'
            agreements[0].acceptance_date = fields.Date.today()
            agreements[0].acceptance_partner_id = partner_id
        return request.redirect('/my/agreements')

    @http.route(
        ['/my/agreements/download/<int:agreement_id>'], type='http',
        auth='user', website=True)
    def portal_my_agreements_download(
            self, agreement_id, access_token=None, **kw):
        agreement_id = self._document_check_access(
            'agreement.acceptance', agreement_id, access_token=access_token)
        name = agreement_id.agreement_template.name
        custom = agreement_id.custom_document
        document = agreement_id.agreement_template.document
        pdf = (
            custom and custom or document
        )
        disposition = 'attachment; filename=%s.pdf' % name
        pdfhttpheaders = [
            ('Content-Type', 'application/pdf'),
            ('Content-Length', len(pdf)),
            ('Content-Disposition', disposition)
        ]
        content_base64 = base64.b64decode(pdf)
        return request.make_response(content_base64, headers=pdfhttpheaders)
