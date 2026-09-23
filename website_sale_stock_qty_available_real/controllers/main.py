###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.addons.website_sale_stock.controllers import main
from odoo.http import request, route


class PaymentPortal(main.PaymentPortal):
    @route()
    def shop_payment_transaction(self, *args, **kwargs):
        website = request.website
        mode = website._get_website_sale_stock_qty_mode()
        if mode != 'available':
            request.website = website.with_context(
                website_sale_stock_qty_mode=mode)
        return super().shop_payment_transaction(*args, **kwargs)
