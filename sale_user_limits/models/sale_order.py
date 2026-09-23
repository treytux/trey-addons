###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, fields, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    state = fields.Selection(
        selection_add=[
            ('pending-approve', 'Pending approve'),
        ],
    )
    amount_approve = fields.Float(
        string='Amount approve',
        copy=False,
        readonly=True,
    )
    exception_limit_reason = fields.Char(
        string='Reason of exception',
        readonly=True,
        copy=False,
    )

    def check_limits(self):
        for sale in self:
            lines = sale.order_line.filtered(lambda ln: not ln.is_limit_ok())
            if lines:
                sale.state = 'pending-approve'
                return False
            if sale.state in ['sale', 'done']:
                return True
            if sale.amount_total == sale.amount_approve:
                return True
            if sale.amount_untaxed <= sale.env.user.sales_amount_limit:
                return True
            sale.exception_limit_reason = _(
                'Total amount is upper that your amount limit (%s), your'
                'manager need to approve this operation') % (
                    sale.env.user.sales_amount_limit)
            sale.state = 'pending-approve'
        return False

    def action_approve(self):
        if self.check_limits():
            self.write({
                'amount_approve': self.amount_total,
                'exception_limit_reason': None,
                'state': 'draft',
            })

    def action_confirm(self):
        if not self.check_limits():
            return False
        res = super().action_confirm()
        if res and self.exception_limit_reason:
            self.exception_limit_reason = None
        return res

    def action_done(self):
        if not self.check_limits():
            return False
        return super().action_done()

    def action_quotation_send(self):
        if not self.check_limits():
            return False
        return super().action_quotation_send()

    def print_quotation(self):
        if not self.check_limits():
            return False
        return super().print_quotation()

    def action_preview_sale_order(self):
        if not self.check_limits():
            return False
        return super().action_preview_sale_order()
