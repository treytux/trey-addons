# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from functools import partial
from openerp import http
from openerp.http import request
from openerp.addons.website_myaccount.controllers.main import MyAccount
import logging
_log = logging.getLogger(__name__)


class MyAccountAgent(MyAccount):
    def _prepare_agent_saleorders(self, saleorder_id=None, season_id=None,
                                  partner_id=None, name=None, limit=None,
                                  order=None):
        env = request.env
        partners = self._prepare_partners()
        user = env['res.users'].sudo().browse(request.uid)
        domain = [
            ('partner_id', 'in', partners and partners.ids or []),
            ('state', 'not in', self._get_except_states()),
            ('order_line.agents.agent', 'in', [user.partner_id.id])]
        if saleorder_id:
            domain.append(('id', '=', saleorder_id))
        if season_id:
            domain.append(('season_id', '=', season_id))
        if partner_id:
            domain.append(('partner_id', '=', partner_id))
        if name:
            domain = domain + [
                ('|'), ('partner_id.name', 'ilike', name),
                ('partner_id.comercial', 'ilike', name)]
        order = order and order or 'partner_id ASC, date_order desc, id desc'
        saleorders = env['sale.order'].sudo().search(
            domain, limit=limit, order=order)
        return saleorders, partners

    def _render_agent_orders(self, sales, seasons, season, partners, partner,
                             name):
            return request.website.render(
                'website_myaccount_agent.orders', {
                    'orders': sales,
                    '_get_pending_states': partial(self._get_pending_states),
                    '_get_confirmed_states': partial(
                        self._get_confirmed_states),
                    'seasons': seasons,
                    'season': season,
                    'partners': partners,
                    'partner': partner,
                    'name': name})

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

    def _get_seasons(self):
        env = request.env
        return env['product.season'].search(
            [], order='date_from DESC, id DESC')

    @http.route([
        '/my/agent/orders',
        '/myaccount/agent/orders',
        '/mi/comercial/pedidos',
        '/micuenta/comercial/pedidos'
    ], type='http', auth='user', website=True)
    def agent_orders(self, **post):
        seasons = self._get_seasons()
        season = seasons and seasons[0].id or None
        season = post.get('season', season)
        season = season and season != '' and int(season) or None
        partner = post.get('partner', None)
        partner = partner and int(partner) or partner
        name = post.get('name', None)
        sales, partners = self._prepare_agent_saleorders(
            season_id=season, partner_id=partner, name=name)
        return self._render_agent_orders(
            sales, seasons, season, partners, partner, name)

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

    def _order_agents(self, saleorder):
        agents = []
        for ol in saleorder.order_line:
            for a in ol.agents:
                agents.append(a.agent.id)
        return list(set(agents))

    @http.route([
        '/my/agent/download/saleorder/<int:saleorder_id>',
        '/myaccount/agent/download/saleorder/<int:saleorder_id>',
        '/mi/comercial/descargar/pedidoventas/<int:saleorder_id>',
        '/micuenta/comercial/descargar/pedidoventas/<int:saleorder_id>'
    ], type='http', auth='user', website=True)
    def agent_download_saleorder(self, saleorder_id, **post):
        env = request.env
        saleorder = env['sale.order'].sudo().browse(saleorder_id)
        if not saleorder:
            return ''
        if saleorder.state in self._get_except_states():
            return ''
        user = env['res.users'].sudo().browse(request.uid)
        if user.partner_id.id not in self._order_agents(saleorder):
            return ''
        pdf = env['report'].sudo().get_pdf(
            saleorder, 'sale.report_saleorder')
        pdfhttpheaders = [('Content-Type', 'application/pdf'),
                          ('Content-Length', len(pdf))]
        return request.make_response(pdf, headers=pdfhttpheaders)

    def _prepare_agent_invoices(self, invoice_id=None, season_id=None,
                                partner_id=None, name=None, limit=None,
                                order=None):
        env = request.env
        partners = self._prepare_partners_and_addresses()
        user = env['res.users'].sudo().browse(request.uid)
        domain = [
            ('partner_id', 'in', partners.ids if partners else []),
            ('state', 'not in', self._get_inv_except_states()),
            ('invoice_line.agents.agent', 'in', [user.partner_id.id])]
        if invoice_id:
            domain.append(('id', '=', invoice_id))
        if season_id:
            domain.append(('season_id', '=', season_id))
        if partner_id:
            domain.append(('partner_id', '=', partner_id))
        if name:
            domain = domain + [
                ('|'), ('partner_id.name', 'ilike', name),
                ('partner_id.comercial', 'ilike', name)]
        order = order and order or 'partner_id ASC, number desc, id desc'
        return (
            env['account.invoice'].sudo().search(
                domain, limit=limit,
                order=order),
            partners)

    def _render_agent_inv(self, invoices, seasons, season, partners, partner,
                          name):
            return request.website.render(
                'website_myaccount_agent.invoices', {
                    'invoices': invoices,
                    '_get_inv_pending_states': partial(
                        self._get_inv_pending_states),
                    '_get_inv_paid_states': partial(self._get_inv_paid_states),
                    'seasons': seasons,
                    'season': season,
                    'partners': partners,
                    'partner': partner,
                    'name': name})

    @http.route([
        '/my/agent/invoices',
        '/myaccount/agent/invoices',
        '/mi/comercial/facturas',
        '/micuenta/comercial/facturas'
    ], type='http', auth='user', website=True)
    def agent_invoices(self, container=None, **post):
        seasons = self._get_seasons()
        season = seasons and seasons[0].id or None
        season = post.get('season', season)
        season = season and season != '' and int(season) or None
        partner = post.get('partner', None)
        partner = partner and int(partner) or partner
        name = post.get('name', None)
        sales, partners = self._prepare_agent_invoices(
            season_id=season, partner_id=partner, name=name)
        return self._render_agent_inv(
            sales, seasons, season, partners, partner, name)

    def _invoice_agents(self, invoice):
        agents = []
        for il in invoice.invoice_line:
            for a in il.agents:
                agents.append(a.agent.id)
        return list(set(agents))

    @http.route([
        '/my/agent/download/invoice/<int:invoice_id>',
        '/myaccount/agent/download/invoice/<int:invoice_id>',
        '/mi/comercial/descargar/factura/<int:invoice_id>',
        '/micuenta/comercial/descargar/factura/<int:invoice_id>'
    ], type='http', auth='user', website=True)
    def agent_download_invoice(self, invoice_id, **post):
        env = request.env
        invoice = env['account.invoice'].sudo().browse(invoice_id)
        if not invoice:
            return ''
        if invoice.state in self._get_inv_except_states():
            return ''
        user = env['res.users'].sudo().browse(request.uid)
        if user.partner_id.id not in self._invoice_agents(invoice):
            return ''
        pdf = env['report'].sudo().get_pdf(
            invoice, 'account.report_invoice')
        pdfhttpheaders = [('Content-Type', 'application/pdf'),
                          ('Content-Length', len(pdf))]
        return request.make_response(pdf, headers=pdfhttpheaders)
