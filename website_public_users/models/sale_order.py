###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.multi
    def _compute_abandoned_cart(self):
        super()._compute_abandoned_cart()
        website = self.env['website'].default_website_get()
        for order in self:
            if (order.is_abandoned_cart and
                    order.partner_id.user_ids in website.website_public_users):
                order.is_abandoned_cart = False
