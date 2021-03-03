###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.addons.website_sale.controllers.main import WebsiteSale
from odoo.http import request


class WebsiteSale(WebsiteSale):
    def _get_shop_payment_values(self, order, **kwargs):
        values = super()._get_shop_payment_values(order=order, **kwargs)
        acquirers = []
        partner = request.env.user.partner_id
        for acquirer in values['acquirers']:
            account_payment_modes = acquirer.sudo().account_payment_mode_ids
            allowed_payment = (
                partner.customer_payment_mode_id in account_payment_modes)
            if not account_payment_modes or allowed_payment:
                acquirers.append(acquirer)
        values['acquirers'] = acquirers
        return values
