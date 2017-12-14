# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from functools import partial
from openerp import http, fields
from openerp.http import request
from openerp.addons.website_myaccount.controllers.main import MyAccount


class MyAccountAgent(MyAccount):
    def _prepare_agent_saleorders(self, saleorder_id=None, limit=None):
        env = request.env
        partners = self._prepare_partners()
        partners = partners.ids if partners else []
        user = env['res.users'].sudo().browse(request.uid)
        domain = [
            ('partner_id', 'in', partners),
            ('state', 'not in', self._get_except_states()),
            ('order_line.agents.agent', 'in', [user.partner_id.id])]
        if saleorder_id:
            domain.append(('id', '=', saleorder_id))
        saleorders = env['sale.order'].sudo().search(domain, limit=limit)
        return saleorders

    def _render_agent_orders(self, sales, list_states, state, year, year_to,
                             year_from, scope):
            return request.website.render(
                'website_myaccount_agent.orders', {
                    'orders': sales,
                    '_get_pending_states': partial(self._get_pending_states),
                    '_get_confirmed_states': partial(
                        self._get_confirmed_states),
                    'states': list_states,
                    'state': state,
                    'year': year,
                    'year_to': year_to,
                    'year_from': year_from,
                    'scope': scope})

    def _prepare_partners(self, limit=None):
        env = request.env
        user = env['res.users'].sudo().browse(request.uid)
        domain = [('agents', 'in', [user.partner_id.id])]
        partners = env['res.partner'].sudo().search(
            domain, order='name ASC', limit=limit)
        return partners

    def _prepare_partners_and_addresses(self, limit=None):
        env = request.env
        user = env['res.users'].sudo().browse(request.uid)
        domain = ['|', ('agents', 'in', [user.partner_id.id]), '&',
                  ('root_partner_id.agents', 'in', [user.partner_id.id]),
                  ('type', '!=', 'contact')]
        partners = env['res.partner'].sudo().search(domain, limit=limit)
        return partners

    def _prepare_partner(self, partner_id):
        env = request.env
        user = env['res.users'].sudo().browse(request.uid)
        domain = [
            ('id', '=', partner_id),
            ('agents', 'in', [user.partner_id.id])]
        partner = env['res.partner'].sudo().search(domain, limit=1)
        return partner if partner else None

    @http.route([
        '/my/agent/orders',
        '/myaccount/agent/orders',
        '/mi/comercial/pedidos',
        '/micuenta/comercial/pedidos'
    ], type='http', auth='user', website=True)
    def agent_orders(self, **post):
        sales = self._prepare_agent_saleorders()
        year_to = fields.Datetime.from_string(fields.Datetime.now()).year
        year_from = year_to
        list_states = self._get_list_states()
        if not post or not sales:
            self._restart_order_fields()
            return self._render_agent_orders(
                sales, list_states, self.state,
                self.year if self.year else year_to,
                year_to, year_from, self.scope)
        if sales and sales[-1].date_order:
            year_from = fields.Datetime.from_string(
                sales[-1].date_order).year
        state = post.get('state') if post.get('state') else None
        scope = post.get('scope') if post.get('scope') else None
        year = post.get('year') if post.get('year') else None
        if state:
            self.state = state
        else:
            state = self.state
        if scope and not year:
            self.scope = scope
            self.year_or_scope = 'scope'
        if year and not scope:
            self.year = year
            self.year_or_scope = 'year'
        if not year and not scope and self.year_or_scope == 'year':
            scope = None
            year = self.year
        if not year and not scope and self.year_or_scope == 'scope':
            year = None
            scope = self.scope
        domain = [('id', 'in', sales.ids)]
        for st in list_states:
            if state == st:
                domain.append(
                    ('state', 'in', tuple((list_states.get(st)['states']))))
        limit = None
        if scope == 'latest':
            limit = 20
        if scope == 'all':
            limit = None
        if year:
            scope = 'no_scope'
            date_from = '%s-01-01 00:00:00' % (year)
            date_to = '%s-12-31 23:59:59' % (year)
            domain.extend([
                ('date_order', '>=', date_from),
                ('date_order', '<=', date_to)])
        sales = request.env['sale.order'].sudo().search(
            domain, limit=limit, order='id DESC')
        return self._render_agent_orders(
            sales, list_states, state, year if year else year_to,
            year_to, year_from, scope)

    @http.route([
        '/my/agent/customers',
        '/myaccount/agent/customers',
        '/mi/comercial/clientes',
        '/micuenta/comercial/clientes'
    ], type='http', auth='user', website=True)
    def agent_customers(self, **post):
        partners = self._prepare_partners()
        return request.website.render(
            'website_myaccount_agent.customers', {
                'partners': partners})

    @http.route([
        '/my/agent/customer/<int:partner_id>',
        '/myaccount/agent/customers/<int:partner_id>',
        '/mi/comercial/clientes/<int:partner_id>',
        '/micuenta/comercial/clientes/<int:partner_id>'
    ], type='http', auth='user', website=True)
    def agent_customer_profile(self, partner_id, **post):
        partner = self._prepare_partner(partner_id)
        if not partner:
            return request.render('website.404')
        return request.website.render(
            'website_myaccount_agent.customer_profile', {
                'partner': partner})

    @http.route([
        '/my/agent/download/saleorder/<int:saleorder_id>',
        '/myaccount/agent/download/saleorder/<int:saleorder_id>',
        '/mi/comercial/descargar/pedidoventas/<int:saleorder_id>',
        '/micuenta/comercial/descargar/pedidoventas/<int:saleorder_id>'
    ], type='http', auth='user', website=True)
    def agent_download_saleorder(self, saleorder_id, **post):
        env = request.env
        saleorder = self._prepare_agent_saleorders(
            saleorder_id=saleorder_id, limit=1)
        if (saleorder):
            pdf = env['report'].sudo().get_pdf(
                saleorder, 'sale.report_saleorder')
            pdfhttpheaders = [('Content-Type', 'application/pdf'),
                              ('Content-Length', len(pdf))]
            return request.make_response(pdf, headers=pdfhttpheaders)
        else:
            return ''

    def _prepare_agent_invoices(self, invoice_id=None, limit=None):
        env = request.env
        partners = self._prepare_partners_and_addresses()
        partners = partners.ids if partners else []
        user = env['res.users'].sudo().browse(request.uid)
        domain = [
            ('partner_id', 'in', partners),
            ('state', 'not in', self._get_inv_except_states()),
            ('invoice_line.agents.agent', 'in', [user.partner_id.id])]
        if invoice_id:
            domain.append(('id', '=', invoice_id))
        return env['account.invoice'].sudo().search(domain, limit=limit)

    def _render_agent_inv(self, invoices, state, states, year, year_to,
                          year_from, scope):
            return request.website.render(
                'website_myaccount_agent.invoices', {
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
        '/my/agent/invoices',
        '/myaccount/agent/invoices',
        '/mi/comercial/facturas',
        '/micuenta/comercial/facturas'
    ], type='http', auth='user', website=True)
    def agent_invoices(self, container=None, **post):
        invoices = self._prepare_agent_invoices()
        inv_year_to = fields.Datetime.from_string(fields.Datetime.now()).year
        inv_year_from = inv_year_to
        inv_list_states = self._get_inv_list_states()
        if not post or not invoices:
            self._restart_invoice_fields()
            return self._render_agent_inv(
                invoices, self.inv_state, inv_list_states,
                self.inv_year if self.inv_year else inv_year_to, inv_year_to,
                inv_year_from, self.inv_scope)
        if invoices and invoices[-1].date_invoice:
            inv_year_from = fields.Datetime.from_string(
                invoices[-1].date_invoice).year
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
        return self._render_agent_inv(
            invoices, inv_state, inv_list_states,
            inv_year if inv_year else inv_year_to, inv_year_to, inv_year_from,
            inv_scope)

    @http.route([
        '/my/agent/download/invoice/<int:invoice_id>',
        '/myaccount/agent/download/invoice/<int:invoice_id>',
        '/mi/comercial/descargar/factura/<int:invoice_id>',
        '/micuenta/comercial/descargar/factura/<int:invoice_id>'
    ], type='http', auth='user', website=True)
    def agent_download_invoice(self, invoice_id, **post):
        env = request.env
        invoice = self._prepare_agent_invoices(invoice_id=invoice_id, limit=1)
        if invoice:
            pdf = env['report'].sudo().get_pdf(
                invoice, 'account.report_invoice')
            pdfhttpheaders = [('Content-Type', 'application/pdf'),
                              ('Content-Length', len(pdf))]
            return request.make_response(pdf, headers=pdfhttpheaders)
        else:
            return ''
