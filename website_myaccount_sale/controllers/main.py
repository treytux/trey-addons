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


class MyAccountSale(MyAccount):
    scope = 'latest'
    year = None
    year_or_scope = 'scope'
    state = None
    except_states = ['draft', 'cancel']
    pending_states = ['draft', 'sent', 'waiting_date']
    confirmed_states = [
        'progress', 'manual', 'shipping_except', 'invoice_except', 'done']
    list_states = {
        'progress': {
            'name': _('Progress'),
            'value': 'progress',
            'states': pending_states},
        'confirmed': {
            'name': _('Confirmed'),
            'value': 'confirmed',
            'states': confirmed_states}}

    def _restart_order_fields(self):
        self.scope = 'latest'
        self.year = None
        self.year_or_scope = 'scope'
        self.state = None

    def _get_except_states(self):
        return self.except_states

    def _get_pending_states(self):
        return self.pending_states

    def _get_confirmed_states(self):
        return self.confirmed_states

    def _get_list_states(self):
        return self.list_states

    def _get_saleorders_domain(self, saleorder_id=None):
        domain = [
            '|',
            ('partner_id', 'in', self._get_partner_ids()),
            ('message_follower_ids', 'in', self._get_follower_ids()),
            ('state', 'not in', self._get_except_states())]
        if saleorder_id:
            domain.append(('id', '=', saleorder_id))
        return domain

    def _prepare_saleorders(self, saleorder_id=None, limit=None):
        env = request.env
        saleorders = env['sale.order'].sudo().search(
            self._get_saleorders_domain(saleorder_id=saleorder_id),
            limit=limit)
        return saleorders

    def _render_orders(self, sales, list_states, state, year, year_to,
                       year_from, scope):
            return request.website.render(
                'website_myaccount_sale.orders', {
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

    @http.route([
        '/my/orders',
        '/myaccount/orders',
        '/mis/pedidos',
        '/micuenta/pedidos'
    ], type='http', auth='user', website=True)
    def orders(self, **post):
        sales = self._prepare_saleorders()
        year_to = fields.Datetime.from_string(fields.Datetime.now()).year
        year_from = year_to
        list_states = self._get_list_states()
        if sales and sales[-1].date_order:
            year_from = fields.Datetime.from_string(
                sales[-1].date_order).year
        if not post:
            self._restart_order_fields()
            return self._render_orders(
                sales, list_states, self.state,
                self.year if self.year else year_to, year_to, year_from,
                self.scope)
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
        return self._render_orders(
            sales, list_states, state, year if year else year_to,
            year_to, year_from, scope)

    @http.route([
        '/my/download/saleorder/<int:saleorder_id>',
        '/myaccount/download/saleorder/<int:saleorder_id>',
        '/mi/descargar/pedidoventas/<int:saleorder_id>',
        '/micuenta/descargar/pedidoventas/<int:saleorder_id>'
    ], type='http', auth='user', website=True)
    def download_saleorder(self, saleorder_id, **post):
        env = request.env
        saleorder = self._prepare_saleorders(
            saleorder_id=saleorder_id, limit=1)
        if (saleorder):
            pdf = env['report'].sudo().get_pdf(
                saleorder, 'sale.report_saleorder')
            pdfhttpheaders = [('Content-Type', 'application/pdf'),
                              ('Content-Length', len(pdf))]
            return request.make_response(pdf, headers=pdfhttpheaders)
        else:
            return ''
