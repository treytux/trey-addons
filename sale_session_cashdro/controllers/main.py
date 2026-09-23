###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import http
from odoo.http import request


class SaleSessionCashdro(http.Controller):
    @http.route(
        ['/session/<int:sale_id>/<int:operation_id>/<int:journal_id>/cancel'],
        type='http', auth='user', website=True)
    def sale_session_cashdro_cancel(
            self, sale_id, operation_id, journal_id, access_token=None):
        context = request.env.context.copy()
        context.update({
            'operation_id': operation_id,
            'journal_id': journal_id,
        })
        request.env.context = context
        request.env['account.journal'].finish_operation()
        sale_menu = request.env.ref('sale.sale_menu_root')
        url = '/web#id=%s&view_type=form&model=sale.order&menu_id=%s' % (
            str(sale_id), sale_menu.id)
        return request.redirect(url)
