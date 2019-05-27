# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields, api


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    date_value = fields.Date(
        string='Value date',
        readonly=True,
        states={'draft': [('readonly', False)]},
        help='Value date to compute due date on sale order invoice.')

    @api.multi
    def onchange_payment_term_date_invoice(
            self, payment_term_id, date_invoice):
        return super(AccountInvoice, self).onchange_payment_term_date_invoice(
            payment_term_id, self.date_value)

    @api.onchange('date_value')
    def onchange_payment_term_date_from_invoice(self):
        if self.date_value:
            res = self.onchange_payment_term_date_invoice(
                self.payment_term.id, self.date_value)
            self.date_due = res['value'].get('date_due')

    @api.multi
    def copy(self, default=None):
        new_invoice = super(AccountInvoice, self).copy(default)
        new_invoice.date_due = self.date_due
        return new_invoice

    @api.multi
    def action_move_create(self):
        res = super(AccountInvoice, self).action_move_create()
        mline_obj = self.env['account.move.line']
        for inv in self.browse(self.ids):
            if inv.date_value and inv.payment_term and inv.move_id:
                move_lines = mline_obj.browse(
                    sorted([mline.id for mline in inv.move_id.line_id
                            if mline.date_maturity]))
                date_lines = inv.payment_term.compute(inv.amount_total,
                                                      inv.date_value or False)
                if move_lines and date_lines:
                    for line in move_lines:
                        line.write({'date_maturity': date_lines[0][0][0]})
                        del date_lines[0][0]
        return res
