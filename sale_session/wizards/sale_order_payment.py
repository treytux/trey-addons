###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class SaleOrderPayment(models.TransientModel):
    _name = 'sale.order.payment'
    _description = 'Wizard to register payments in a sale order'

    def _get_default_sale_order(self):
        return self.env['sale.order'].browse(self._context['active_id'])

    sale_id = fields.Many2one(
        comodel_name='sale.order',
        string='Sale Order',
        default=_get_default_sale_order,
        required=True,
    )
    journal_id = fields.Many2one(
        comodel_name='account.journal',
        string='Payment journal',
        required=True,
    )
    currency_id = fields.Many2one(
        related='sale_id.currency_id',
    )
    amount_total = fields.Monetary(
        related='sale_id.amount_total',
        string='Total',
    )
    amount = fields.Monetary(
        string='Amount paid',
    )
    money_back = fields.Monetary(
        string='Money back',
        compute='_compute_money_back'
    )

    @api.depends('amount')
    def _compute_money_back(self):
        for wizard in self:
            wizard.money_back = wizard.amount - wizard.sale_id.amount_total

    def action_confirm(self):
        self.ensure_one()
        self.sale_id.session_pay(self.amount, self.journal_id)
        return {'type': 'ir.actions.act_window_close'}
