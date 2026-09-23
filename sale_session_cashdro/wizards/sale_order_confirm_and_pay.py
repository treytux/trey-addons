###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models


class SaleOrderConfirmAndPay(models.TransientModel):
    _inherit = 'sale.order.confirm_and_pay'

    def action_pay(self):
        if self.journal_id and self.journal_id.type == 'cash' and (
                self.journal_id.check_cashdro_config()):
            self.sale_id.session_confirm_and_create_invoice()
            action = self.env.ref(
                'sale_session_cashdro.sale_session_cashdro_action')
            context = self.env.context.copy()
            context.update({
                'sale_id': self.sale_id.id,
                'journal_id': self.journal_id.id,
                'sale_amount': self.amount_total,
                'amount_paid': self.amount,
                'session_id': self.sale_id.session_id.id,
            })
            vals = action.read()[0]
            vals['context'] = context
            return vals
        return super().action_pay()

    def _compute_need_change_amount(self):
        super()._compute_need_change_amount()
        for sale in self.filtered(lambda s: s.need_change_amount):
            sale.need_change_amount = not bool(sale.journal_id.cashdro_host)
