###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class AccountInvoicePaymentCashdro(models.TransientModel):
    _name = 'account.invoice.payment.cashdro'
    _description = 'Wizard to pay invoice with Cashdro'

    invoice_id = fields.Many2one(
        comodel_name='account.invoice',
        string='Invoice',
    )
    sale_id = fields.Many2one(
        comodel_name='sale.order',
        string='Sale order',
    )
    session_id = fields.Many2one(
        comodel_name='sale.session',
        string='Sale session',
    )
    payment_journal_ids = fields.Many2many(
        comodel_name='account.journal',
        relation='account_journal2account_invoice_cashdro_rel',
        column1='journal_id',
        column2='wizard_id',
        string='Payment journals',
    )
    journal_id = fields.Many2one(
        comodel_name='account.journal',
        domain='[("id", "in", payment_journal_ids)]',
        string='Payment journal',
    )

    @api.model
    def default_get(self, fields):
        res = super().default_get(fields)
        invoice = self.env['account.invoice'].browse(
            self.env.context.get('active_ids', []))
        sale = self.env['sale.order'].search([
            ('name', '=', invoice.origin.split(',')[0].strip()),
        ], limit=1)
        res.update({
            'invoice_id': invoice.id,
            'sale_id': sale.id,
            'session_id': sale.session_id.id,
            'payment_journal_ids': [
                (6, 0, sale.session_id.team_id.payment_journal_ids.ids)],
        })
        return res

    def action_pay_invoice_cashdro(self):
        if self.journal_id and self.journal_id.type == 'cash' and (
                self.journal_id.check_cashdro_config()):
            action = self.env.ref(
                'sale_session_cashdro.sale_session_cashdro_action')
            context = self.env.context.copy()
            if not self.invoice_id.origin:
                return
            context.update({
                'sale_id': self.sale_id.id,
                'journal_id': self.journal_id.id,
                'sale_amount': self.invoice_id.amount_total,
                'amount_paid': self.invoice_id.amount_total,
                'session_id': self.session_id.id,
            })
            vals = action.read()[0]
            vals['context'] = context
            return vals
