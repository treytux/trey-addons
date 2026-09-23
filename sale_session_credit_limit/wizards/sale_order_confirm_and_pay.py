###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models


class SaleOrderConfirmAndPay(models.TransientModel):
    _inherit = 'sale.order.confirm_and_pay'

    def action_pay(self):
        self = self.with_context(skip_financial_risk_sale_session=True)
        return super(SaleOrderConfirmAndPay, self).action_pay()

    def action_confirm(self):
        self = self.with_context(skip_financial_risk_sale_session=True)
        return super(SaleOrderConfirmAndPay, self).action_confirm()
