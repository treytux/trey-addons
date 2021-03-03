###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.http import request
from odoo.addons.website_sale.controllers.main import WebsiteSale


class WebsiteSale(WebsiteSale):
    def _show_acquirer(self, fa):
        if fa.environment == 'prod':
            return True
        groups_id = request.env.user.groups_id
        if request.env.ref('website.group_website_designer') in groups_id:
            return True
        return False

    def _get_shop_payment_values(self, order, **kwargs):
        res = super(WebsiteSale, self)._get_shop_payment_values(
            order=order, **kwargs)
        res['form_acquirers'] = [
            fa for fa in res['form_acquirers'] if self._show_acquirer(fa)
        ]
        return res
