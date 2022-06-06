###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.addons.website_sale.controllers.main import WebsiteSale


class WebsiteSale(WebsiteSale):
    def add_payment_acquirer(self, acquirer, order):
        return acquirer.provider != 'direct_order' or (
            order.risk_exception_msg() == ''
            and order.partner_id.credit_limit > 0)

    def _get_shop_payment_values(self, order, **kwargs):
        values = super()._get_shop_payment_values(order=order, **kwargs)
        values['acquirers'] = [
            acq for acq in values['acquirers'] if (
                self.add_payment_acquirer(acq, order))]
        return values
