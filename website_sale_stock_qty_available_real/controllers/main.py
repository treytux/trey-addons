###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.addons.website_sale_stock.controllers.main import WebsiteSale
from odoo.http import request, route


class WebsiteSale(WebsiteSale):
    @route()
    def payment_transaction(self, *args, **kwargs):
        request.website = request.website.with_context(
            website_sale_stock_available_real=True)
        return super().payment_transaction(*args, **kwargs)
