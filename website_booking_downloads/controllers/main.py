# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
import base64
from openerp import http
from openerp.http import request
import logging
_log = logging.getLogger(__name__)

DUMMY_CHARS = 4


class WebsiteBookingDownloads(http.Controller):
    def _prepare_invoice(self, token, log=False):
        # Request invoice for
        #   booking: EV7Q185J
        #   date: 2018-07-12
        # With base64.b64encode('EV7Q185J,2018-07-12') we obtain
        #   token: RVY3UTE4NUosMjAxOC0wNy0xMg==
        # Add 4 dummy characters before and after token
        #   token: EWKKRVY3UTE4NUosMjAxOC0wNy0xMg==3Art
        # And now we call to URL
        #   [domain][route]?token=EWKKRVY3UTE4NUosMjAxOC0wNy0xMg==3Art
        data = base64.b64decode(token[DUMMY_CHARS:-1 * DUMMY_CHARS]).split(',')
        if len(data) < 2:
            return False
        if log:
            _log.info('X' * 80)
            _log.info(('booking', data[0]))
            _log.info('X' * 80)
            _log.info(('date', data[1]))
        invoice = request.env['account.invoice'].sudo().search([
            ('type', '=', 'out_invoice'),
            ('state', 'in', ['open', 'paid']),
            ('booking_id.name', '=', data[0])])
        if not invoice:
            return False
        return data[1] == invoice.booking_id.date[:10] and invoice or False

    @http.route([
        '/booking/download/invoice'], type='http', auth='public', website=True)
    def download_booking_invoice(self, token, log=False):
        invoice = self._prepare_invoice(token, log)
        if not invoice:
            return ''
        pdf = request.env['report'].sudo().get_pdf(
            invoice, 'account.report_invoice')
        headers = [
            ('Content-Type', 'application/pdf'),
            ('Content-Length', len(pdf))]
        return request.make_response(pdf, headers=headers)
