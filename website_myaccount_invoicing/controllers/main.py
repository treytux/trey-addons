# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.

from openerp import http
from openerp.http import request
import logging
_log = logging.getLogger(__name__)
try:
    from openerp.addons.website_myaccount.controllers.main import MyAccount
except ImportError:
    MyAccount = object
    _log.error('No module named website_myaccount')


class MyAccountInvoicing(MyAccount):
    def is_paid(self, invoice):
        if invoice.state == 'paid':
            return True
        else:
            return False

    def payment_mode_install(self):
        '''Checks if exists the 'Payment mode' field in the invoice'''
        if 'payment_mode_id' not in request.env['account.invoice']._columns:
            return False
        return True

    @http.route([
        '/my/invoicing',
        '/myaccount/invoicing',
        '/mi/facturacion',
        '/micuenta/facturacion'
    ], type='http', auth='user', website=True)
    def invoicing(self, **post):
        env = request.env

        partner = self._get_partner_company()
        if partner:
            orders = env['sale.order'].search(
                [('partner_id', '=', partner.id),
                 ('state', 'not in', ['draft', 'sent', 'cancel'])])
            invoice_ids = []
            for o in orders:
                if o.invoice_ids:
                    invoice_ids = invoice_ids + o.invoice_ids.ids
            invoice_ids = list(set(invoice_ids))
            invoices = env['account.invoice'].search(
                [('id', 'not in', invoice_ids),
                 ('partner_id', '=', partner.id),
                 ('state', 'not in', ['draft', 'cancel'])])
        else:
            orders = []
            invoices = []
        return request.website.render(
            'website_myaccount_invoicing.invoicing', {
                'orders': orders,
                'invoices': invoices,
                'is_paid': self.is_paid,
                'payment_mode_install': self.payment_mode_install})

    @http.route([
        '/my/invoicing/download/order/<int:order_id>',
        '/myaccount/invoicing/download/order/<int:order_id>',
        '/mi/facturacion/descargar/pedido/<int:order_id>',
        '/micuenta/facturacion/descargar/pedido/<int:order_id>'
    ], type='http', auth='user', website=True)
    def order_download(self, order_id, **post):
        env = request.env
        order = env['sale.order'].browse(order_id)
        if order.exists() and order.partner_id.id == env.user.partner_id.id:
            pdf = env['report'].get_pdf(order, 'sale.report_saleorder')
            pdfhttpheaders = [('Content-Type', 'application/pdf'),
                              ('Content-Length', len(pdf))]
            return request.make_response(pdf, headers=pdfhttpheaders)
        else:
            return ''

    @http.route([
        '/my/invoicing/download/invoice/<int:invoice_id>',
        '/myaccount/invoicing/download/invoice/<int:invoice_id>',
        '/mi/facturacion/descargar/factura/<int:invoice_id>',
        '/micuenta/facturacion/descargar/factura/<int:invoice_id>'
    ], type='http', auth='user', website=True)
    def invoice_download(self, invoice_id, **post):
        env = request.env
        invoice = env['account.invoice'].browse(invoice_id)
        if (invoice.exists() and
                invoice.partner_id.id == env.user.partner_id.id):
            pdf = env['report'].get_pdf(invoice, 'account.report_invoice')
            pdfhttpheaders = [('Content-Type', 'application/pdf'),
                              ('Content-Length', len(pdf))]
            return request.make_response(pdf, headers=pdfhttpheaders)
        else:
            return ''
