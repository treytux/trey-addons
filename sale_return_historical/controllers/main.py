###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import http
from odoo.addons.portal.controllers.mail import PortalChatter
from odoo.addons.portal.controllers.portal import CustomerPortal
from odoo.http import request


class OrderHistoryCustomerPortal(CustomerPortal):
    def _get_order_history_domain(self):
        partner_id = request.env.user.sudo().partner_id
        return [
            '|',
            ('partner_id', 'in', [
                partner_id.id,
                partner_id.commercial_partner_id.id,
            ]),
            ('message_follower_ids', 'in', [
                partner_id.id,
                partner_id.commercial_partner_id.id,
            ]),
        ]

    def _prepare_portal_layout_values(self):
        values = super()._prepare_portal_layout_values()
        OrderHistory = request.env['sale.order.historical']
        order_history_count = OrderHistory.search_count(
            self._get_order_history_domain())
        values.update({
            'order_history_count': order_history_count,
        })
        return values

    @http.route([
        '/my/order/history',
    ], type='http', auth='user', website=True)
    def portal_my_order_history(self, **kw):
        order_obj = request.env['sale.order.historical']
        order_domain = self._get_order_history_domain()
        order_domain_order = 'date_invoiced desc,create_date desc,id desc'
        orders = order_obj.sudo().search(
            order_domain, order=order_domain_order)
        values = {
            'page_name': 'order_history',
            'orders': orders,
        }
        return request.render(
            'sale_return_historical.portal_my_order_history', values)

    @http.route([
        '/my/order/history/<int:order_id>',
    ], type='http', auth='user', website=True)
    def portal_my_order(self, order_id, access_token=None, **kw):
        order_id = self._document_check_access(
            'sale.order.historical', order_id, access_token=access_token)
        values = {
            'page_name': 'order_history',
            'page_name_2': 'sale_order_historical',
            'order': order_id,
        }
        return request.render(
            'sale_return_historical.portal_order', values)

    @http.route([
        '/my/order/history/return/<int:order_line_id>',
    ], type='http', auth='user', website=True)
    def portal_my_order_history_return(
            self, order_line_id, access_token=None, **post):
        order_line_obj = request.env['sale.order.historical.line']
        partner_id = request.env.user.sudo().partner_id
        line = order_line_obj.search([
            '|',
            ('order_id.partner_id', 'in', [
                partner_id.id,
                partner_id.commercial_partner_id.id,
            ]),
            ('order_id.message_follower_ids', 'in', [
                partner_id.id,
                partner_id.commercial_partner_id.id,
            ]),
            ('id', '=', order_line_id),
        ])
        line.update({
            'state': 'pending',
        })
        template = request.env.ref(
            'sale_return_historical.email_template_sale_return_historical')
        template.sudo().with_context(
            lang=request.env.user.lang).send_mail(line.id)
        if post:
            res_id = line.order_id.id
            res_model = 'sale.order.historical'
            message = line.product_id.name + ' : ' + post.get('message')
            PortalChatter.portal_chatter_post(
                self, res_model, res_id, message)
        return request.redirect('/my/order/history')

    @http.route([
        '/my/order/history/label/<int:order_line_id>',
    ], type='http', auth='user', website=True)
    def print_address_label(self, order_line_id, access_token=None, **kw):
        order_line = self._document_check_access(
            'sale.order.historical.line', order_line_id,
            access_token=access_token)
        reference = request.env.ref(
            'sale_return_historical.action_report_return_label')
        pdf = reference.sudo().render_qweb_pdf([order_line.id])[0]
        pdfhttpheaders = [
            ('Content-Type', 'application/pdf'),
            ('Content-Length', len(pdf)),
        ]
        return request.make_response(pdf, headers=pdfhttpheaders)
