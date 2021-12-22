###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from datetime import datetime

from odoo import api, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.model
    def validity_auto_cancel(self):
        sale_orders = self.env['sale.order'].search([
            ('state', '=', 'sent'),
            ('validity_date', '<', datetime.now().strftime('%Y-%m-%d'))
        ])
        for order in sale_orders:
            order.action_cancel()
