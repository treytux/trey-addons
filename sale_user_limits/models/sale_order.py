###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, api, fields, models


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
        self.ensure_one()
        lines = self.order_line.filtered(lambda l: not l.is_limit_ok())
        if lines:
            self.state = 'pending-approve'
            return False
        if self.state in ['sale', 'done']:
            return True
        if self.amount_total == self.amount_approve:
            return True
        if self.amount_untaxed <= self.env.user.sales_amount_limit:
            return True
        self.exception_limit_reason = _(
            'Total amount is upper that your amount limit (%s), your manager '
            'need to approve this operation') % (
                self.env.user.sales_amount_limit)
        self.state = 'pending-approve'
        return False

    @api.multi
    def action_approve(self):
        if self.check_limits():
            self.write({
                'amount_approve': self.amount_total,
                'exception_limit_reason': None,
                'state': 'draft',
            })

    @api.multi
    def action_confirm(self):
        if not self.check_limits():
            return False
        return super().action_confirm()

    @api.multi
    def action_done(self):
        if not self.check_limits():
            return False
        return super().action_done()

    @api.multi
    def action_quotation_send(self):
        if not self.check_limits():
            return False
        return super().action_quotation_send()

    @api.multi
    def print_quotation(self):
        if not self.check_limits():
            return False
        return super().print_quotation()

    @api.multi
    def preview_sale_order(self):
        if not self.check_limits():
            return False
        return super().preview_sale_order()
