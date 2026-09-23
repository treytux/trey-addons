###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.model
    def json_import(self, json_content):
        self = self.with_context(avoid_credit_limit=True)
        return super(SaleOrder, self).json_import(json_content=json_content)

    @api.multi
    def action_confirm(self):
        if self.env.context.get('avoid_credit_limit', False):
            return super(
                SaleOrder, self.with_context(bypass_risk=True)).action_confirm()
        return super().action_confirm()
