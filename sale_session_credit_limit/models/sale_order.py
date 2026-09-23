###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.multi
    def action_confirm(self):
        if self.env.context.get('skip_financial_risk_sale_session', False):
            return super(
                SaleOrder, self.with_context(bypass_risk=True)).action_confirm()
        return super().action_confirm()
