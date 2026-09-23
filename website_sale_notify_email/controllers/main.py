##############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
##############################################################################
from odoo import http
from odoo.addons.website_sale.controllers.main import WebsiteSale
from odoo.http import request


class WebsiteSaleNewOrderNotice(WebsiteSale):

    def _notify_new_sale(self):
        sale_order_id = request.session.get('sale_last_order_id')
        if request.website.notification_type != 'email':
            return False
        template = request.env.ref(
            'website_sale_notify_email.mail_template_new_website_order',
            raise_if_not_found=False,
        )
        if template:
            template.sudo().with_context().send_mail(
                sale_order_id, force_send=True)

    @http.route()
    def payment_confirmation(self, **post):
        res = super().payment_confirmation(**post)
        if request.website.notify_new_sale:
            self._notify_new_sale()
        return res
