###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models, api


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    state = fields.Selection(
        selection_add=[
            ('pending-approve', 'Pending approve'),
        ],
    )
    amount_approve = fields.Float(
        string='Amount approve',
        readonly=True,
    )

    def check_approve(self):
        self.ensure_one()
        lines = self.order_line.filtered(lambda l: not l.check_approve())
        if lines:
            self.state = 'pending-approve'
            return False
        if self.amount_total == self.amount_approve:
            return True
        if self.amount_untaxed <= self.env.user.sales_amount_limit:
            return True
        self.state = 'pending-approve'
        return False

    @api.multi
    def action_approve(self):
        if not self.check_approve():
            return False
        self.write({
            'amount_approve': self.amount_total,
            'state': 'draft',
        })

    @api.multi
    def _action_confirm(self):
        if not self.check_approve():
            return False
        return super()._action_confirm()

    @api.multi
    def action_quotation_send(self):
        if not self.check_approve():
            return False
        return super().action_quotation_send()

    @api.multi
    def print_quotation(self):
        if not self.check_approve():
            return False
        return super().print_quotation()

    @api.multi
    def preview_sale_order(self):
        if not self.check_approve():
            return False
        return super().preview_sale_order()
