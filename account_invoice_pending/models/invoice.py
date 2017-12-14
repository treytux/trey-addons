# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, api, fields


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    state = fields.Selection(
        selection_add=[('pending', 'Pending')])
    date_invoice = fields.Date(
        states={'draft': [('readonly', False)],
                'pending': [('readonly', False)]})

    @api.one
    @api.depends(
        'state', 'currency_id', 'invoice_line.price_subtotal',
        'move_id.line_id.account_id.type',
        'move_id.line_id.amount_residual',
        'move_id.line_id.amount_residual_currency',
        'move_id.line_id.currency_id',
        'move_id.line_id.reconcile_partial_id.line_partial_ids.invoice.type')
    def _compute_residual(self):
        if self.state == 'pending':
            self.residual = self.amount_total
        else:
            return super(AccountInvoice, self)._compute_residual()

    @api.multi
    def action_pending(self):
        self.ensure_one()
        if self.partner_id not in self.message_follower_ids:
            self.message_subscribe([self.partner_id.id])
        self.state = 'pending'
