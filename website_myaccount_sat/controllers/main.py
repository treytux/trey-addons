# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.

from openerp import http
from openerp.http import request
from datetime import datetime
import werkzeug
import logging
_log = logging.getLogger(__name__)
try:
    from openerp.addons.website_myaccount.controllers.main import MyAccount
except ImportError:
    MyAccount = object
    _log.error('No module named website_myaccount')


class MyAccountSAT(MyAccount):
    @http.route([
        '/my/sat/claims',
        '/myaccount/sat/claims',
        '/mi/sat/reclamaciones',
        '/micuenta/sat/reclamaciones'
    ], type='http', auth='user', website=True)
    def claims(self, **post):
        partner = self._get_partner_company()
        if not partner:
            return werkzeug.exceptions.abort(404)
        domain = [('partner_sat_id', '=', partner.id)]
        search = request.params.get('search', '')
        state = 'all'
        if search != '':
            domain += [
                '|', '|',
                ('partner_id.name', 'ilike', search),
                ('partner_id.zip', 'ilike', search),
                ('sold_id.lot_id.name', 'ilike', search)]
        else:
            state = request.params.get('state', 'draft')
        if state != 'all':
            domain += [('state', '=', state)]
        return request.website.render(
            'website_myaccount_sat.claims', {
                'claims': request.env['crm.claim'].sudo().search(domain),
                'state': state,
                'search': search})

    @http.route([
        '/my/sat/claim/download/<int:claim_id>',
        '/myaccount/sat/claim/download/<int:claim_id>',
        '/mi/sat/reclamacion/descargar/<int:claim_id>',
        '/micuenta/sat/reclamacion/descargar/<int:claim_id>'],
        type='http', auth='user', website=True)
    def invoice_download(self, claim_id, **post):
        env = request.env
        claim = env['crm.claim'].browse(claim_id)
        partner = self._get_partner_company()
        if not claim.exists() or claim.partner_sat_id.id != partner.id:
            return ''
        if not claim.print_date:
            claim.print_date = datetime.now()
        pdf = env['report'].get_pdf(
            claim, 'print_formats_claim.report_crm_claim')
        return request.make_response(pdf, headers=[
            ('Content-Type', 'application/pdf'), ('Content-Length', len(pdf))])

    @http.route([
        '/my/sat/claim-to/<int:claim_id>/<string:state>',
        '/myaccount/sat/claim-to/<int:claim_id>/<string:state>',
        '/micuenta/sat/reclamacion-a/<int:claim_id>/<string:state>',
        '/mi/sat/reclamacion-a/<int:claim_id>/<string:state>'],
        type='http', auth='user', methods=['GET'], website=True)
    def claim_to(self, claim_id, state, **post):
        env = request.env
        partner = self._get_partner_company()
        if not partner:
            return request.not_found()
        claim = env['crm.claim'].browse(int(claim_id))
        if claim.exists() and claim.partner_sat_id.id == partner.id:
            if state == 'progress':
                claim.to_progress()
            elif state == 'pending_material':
                claim.to_pending_material()
            elif state == 'exception':
                claim.to_exception()
            elif state == 'done':
                claim.to_done()
            return request.redirect('/myaccount/sat/claim/%s' % claim_id)
        return request.not_found()

    @http.route([
        '/my/sat/claim/<int:claim_id>',
        '/myaccount/sat/claim/<int:claim_id>',
        '/mi/sat/reclamacion/<int:claim_id>',
        '/micuenta/sat/reclamacion/<int:claim_id>'],
        type='http', auth='user', methods=['GET', 'POST'], website=True)
    def claim(self, claim_id, **post):
        env = request.env
        partner = self._get_partner_company()
        claim = env['crm.claim'].browse(int(claim_id))
        if not partner or not claim.exists() \
                and claim.partner_sat_id.id != partner.id:
            return request.not_found()
        if not claim.access_date:
            claim.print_date = datetime.now()
        params = request.params
        if params.get('mode', '') == 'write':
            claim.user_fault = params.get('user_fault', '')
            claim.sat_observations = params.get('sat_observations', '')
        elif params.get('mode', '') == 'send':
            claim.with_context(mail_post_autofollow=False).message_post(
                body=params.get('body_html', ''),
                partner_ids=claim.message_follower_ids.ids)
        elif params.get('mode', '') == 'upload':
            files = request.httprequest.files.getlist('attachment')
            c_file = files[0]
            data = c_file.read()
            env['ir.attachment'].create({
                'res_model': 'crm.claim',
                'res_id': claim.id,
                'datas_fname': c_file.filename,
                'datas': data.encode('base64'),
                'name': c_file.filename})
        return request.website.render('website_myaccount_sat.claim', {
            'claim': claim,
            'tab': params.get('tab', 'data'),
            'attachments': env['ir.attachment'].search([
                ('res_model', '=', 'crm.claim'),
                ('res_id', '=', claim.id)],
                order='create_date desc'),
            'mail_messages': env['mail.message'].search([
                ('model', '=', 'crm.claim'),
                ('res_id', '=', claim.id),
                ('type', 'in', ['email', 'notification'])],
                order='date desc')})

    @http.route([
        '/my/sat/claim-stage/<int:claim_id>/<int:claim_stage_id>',
        '/myaccount/sat/claim-stage/<int:claim_id>/<int:claim_stage_id>',
        '/mi/sat/reclamacion-etapa/<int:claim_id>/<int:claim_stage_id>',
        '/micuenta/sat/reclamacion-etapa/<int:claim_id>/<int:claim_stage_id>'],
        type='http', auth='user', website=True)
    def set_claim_stage(self, claim_id, claim_stage_id, **post):
        env = request.env
        claim = env['crm.claim'].browse(claim_id)
        claim_stage = env['crm.claim.stage'].browse(claim_stage_id)
        partner = self._get_partner_company()
        if claim.exists() and claim_stage.exists() \
                and claim.partner_sat_id.id == partner.id:
            return request.redirect('/myaccount/sat/claim/%s' % claim_id)
        return request.not_found()

    @http.route([
        '/my/sat/order/<int:claim_id>/<int:order_id>',
        '/myaccount/sat/order/<int:claim_id>/<int:order_id>',
        '/mi/sat/pedido/<int:claim_id>/<int:order_id>',
        '/micuenta/sat/pedido/<int:claim_id>/<int:order_id>'],
        type='http', auth='user', website=True)
    def order(self, claim_id, order_id, **post):
        partner = self._get_partner_company()
        claim = request.env['crm.claim'].browse(int(claim_id))
        order = request.env['sale.order'].browse(int(order_id))
        if not partner or not claim.exists() or not order.exists():
            return request.not_found()
        return request.website.render('website_myaccount_sat.order',
                                      {'claim': claim, 'order': order})

    @http.route([
        '/my/sat/new-order/<int:claim_id>',
        '/myaccount/sat/new-order/<int:claim_id>',
        '/mi/sat/nuevo-pedido/<int:claim_id>',
        '/micuenta/sat/nuevo-pedido/<int:claim_id>'],
        type='http', auth='user', website=True)
    def new_order(self, claim_id, **post):
        partner = self._get_partner_company()
        claim = request.env['crm.claim'].browse(int(claim_id))
        if not partner or not claim.exists() \
                or claim.partner_sat_id.id != partner.id:
            return request.not_found()
        if not request.params.get('mode', '') == 'write':
            return request.website.render('website_myaccount_sat.new_order',
                                          {'claim': claim, 'partner': partner})
        lines = {}
        for k, v in request.params.iteritems():
            if 'product_id-' in k and int(v) > 0:
                lines[int(k.split('-')[1])] = int(v)
        if lines:
            products = request.env['product.product'].search(
                [('id', 'in', lines.keys())])
            order = request.env['sale.order'].create(
                {'partner_id': partner.id})
            for p in products:
                request.env['sale.order.line'].create({
                    'product_id': p.id,
                    'name': p.name,
                    'product_uom_qty': lines[p.id],
                    'order_id': order.id})
                claim.order_ids = [(4, order.id)]
        return request.redirect('/myaccount/sat/claim/%s' % claim_id)
