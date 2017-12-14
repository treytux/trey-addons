# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from functools import partial
from openerp import http, fields
from openerp.http import request
from openerp.tools.translate import _
try:
    from openerp.addons.website_myaccount.controllers.main import MyAccount
except ImportError:
    MyAccount = object


class MyAccountInvoice(MyAccount):
    inv_scope = 'latest'
    inv_year = None
    inv_year_or_scope = 'scope'
    inv_state = None
    inv_except_states = ['draft', 'cancel']
    inv_pending_states = ['proforma', 'proforma2', 'open']
    inv_paid_states = ['paid']
    inv_list_states = {
        'pending': {
            'name': _('Pending'),
            'value': 'pending',
            'states': inv_pending_states},
        'paid': {
            'name': _('Paid'),
            'value': 'paid',
            'states': inv_paid_states}}

    def _restart_invoice_fields(self):
        self.inv_scope = 'latest'
        self.inv_year = None
        self.inv_year_or_scope = 'scope'
        self.inv_state = None

    def _get_inv_except_states(self):
        return self.inv_except_states

    def _get_inv_pending_states(self):
        return self.inv_pending_states

    def _get_inv_paid_states(self):
        return self.inv_paid_states

    def _get_inv_list_states(self):
        return self.inv_list_states

    def _prepare_invoices(self, invoice_id=None, limit=None):
        env = request.env
        domain = [
            '|',
            ('partner_id', 'in', self._get_partner_ids()),
            ('message_follower_ids', 'in', self._get_follower_ids()),
            ('state', 'not in', self._get_inv_except_states())]
        if invoice_id:
            domain.append(('id', '=', invoice_id))
        return env['account.invoice'].sudo().search(domain, limit=limit)

    def _render_inv(self, invoices, state, states, year, year_to,
                    year_from, scope):
            return request.website.render(
                'website_myaccount_invoice.invoices', {
                    'invoices': invoices,
                    '_get_inv_pending_states': partial(
                        self._get_inv_pending_states),
                    '_get_inv_paid_states': partial(self._get_inv_paid_states),
                    'states': states,
                    'state': state,
                    'year': year,
                    'year_to': year_to,
                    'year_from': year_from,
                    'scope': scope})

    @http.route([
        '/my/invoices',
        '/myaccount/invoices',
        '/mis/facturas',
        '/micuenta/facturas'
    ], type='http', auth='user', website=True)
    def invoices(self, container=None, **post):
        invoices = self._prepare_invoices()
        inv_year_to = fields.Datetime.from_string(fields.Datetime.now()).year
        inv_year_from = inv_year_to
        inv_list_states = self._get_inv_list_states()
        if invoices and invoices[-1].date_invoice:
            inv_year_from = fields.Datetime.from_string(
                invoices[-1].date_invoice).year
        if not post:
            self._restart_invoice_fields()
            return self._render_inv(
                invoices, self.inv_state, inv_list_states,
                self.inv_year if self.inv_year else inv_year_to, inv_year_to,
                inv_year_from, self.inv_scope)
        inv_state = post.get('state') if post.get('state') else None
        inv_scope = post.get('scope') if post.get('scope') else None
        inv_year = post.get('year') if post.get('year') else None
        if inv_state:
            self.inv_state = inv_state
        else:
            inv_state = self.inv_state
        if inv_scope and not inv_year:
            self.inv_scope = inv_scope
            self.inv_year_or_scope = 'scope'
        if inv_year and not inv_scope:
            self.inv_year = inv_year
            self.inv_year_or_scope = 'year'
        if not inv_year and not inv_scope and self.inv_year_or_scope == 'year':
            inv_scope = None
            inv_year = self.inv_year
        if not inv_year and not inv_scope and (
                self.inv_year_or_scope == 'scope'):
            inv_year = None
            inv_scope = self.inv_scope
        domain = [('id', 'in', invoices.ids)]
        for st in inv_list_states:
            if inv_state == st:
                domain.append((
                    'state', 'in', tuple((inv_list_states.get(st)['states']))))
        inv_limit = None
        if inv_scope == 'latest':
            inv_limit = 20
        if inv_scope == 'all':
            inv_limit = None
        if inv_year:
            inv_scope = 'no_scope'
            date_from = '%s-01-01 00:00:00' % (
                inv_year if inv_year else inv_year_to)
            date_to = '%s-12-31 23:59:59' % (
                inv_year if inv_year else inv_year_to)
            domain.extend([
                ('date_invoice', '>=', date_from),
                ('date_invoice', '<=', date_to)])
        invoices = request.env['account.invoice'].sudo().search(
            domain, limit=inv_limit, order='id DESC')
        return self._render_inv(
            invoices, inv_state, inv_list_states,
            inv_year if inv_year else inv_year_to, inv_year_to, inv_year_from,
            inv_scope)

    @http.route([
        '/my/download/invoice/<int:invoice_id>',
        '/myaccount/download/invoice/<int:invoice_id>',
        '/mi/descargar/factura/<int:invoice_id>',
        '/micuenta/descargar/factura/<int:invoice_id>'
    ], type='http', auth='user', website=True)
    def download_invoice(self, invoice_id, **post):
        env = request.env
        invoice = self._prepare_invoices(invoice_id=invoice_id, limit=1)
        if invoice:
            pdf = env['report'].sudo().get_pdf(
                invoice, 'account.report_invoice')
            pdfhttpheaders = [('Content-Type', 'application/pdf'),
                              ('Content-Length', len(pdf))]
            return request.make_response(pdf, headers=pdfhttpheaders)
        else:
            return ''


class MyAccountAccounting(MyAccount):
    def _prepare_banks(self, bank_id=None, limit=None):
        env = request.env
        domain = [
            ('partner_id', 'in', [
                env.user.partner_id.id,
                env.user.partner_id.parent_id.id])]
        if bank_id:
            domain.append(('id', '=', bank_id))
        banks = request.env['res.partner.bank'].sudo().search(
            domain, limit=limit)
        return banks

    @http.route([
        '/my/accounting',
        '/myaccount/accounting',
        '/mi/contabilidad',
        '/micuenta/contabilidad'
    ], type='http', auth='user', website=True)
    def accounting(self, container=None, **post):
        return request.website.render('website_myaccount_invoice.accounting', {
            'user': request.env.user,
            'banks': self._prepare_banks()})
