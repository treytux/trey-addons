# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.
from openerp import models, fields, api, _


class ManualInvoice(models.TransientModel):
    _name = 'wiz.fees_manual.invoice'
    _description = 'Create manual invoice for financing.'

    amount_pending = fields.Float(
        string='Amount pending to invoice',
        readonly=True
    )
    amount = fields.Float(
        string='Amount',
        required=True
    )
    fees_id = fields.Many2one(
        comodel_name='agreement.fees',
        string='Payment financing'
    )
    date_invoice = fields.Date(
        string='Invoice date',
        default=fields.Date.today())
    tax_ids = fields.Many2many(
        comodel_name='account.tax',
        relation='agreement_fees_wizard_manual_invoice_tax_rel',
        column1='wizard_id',
        column2='tax_id',
        domain=[('type_tax_use', '=', 'sale')])

    # @api.constrains('amount')
    # @api.one
    # def _check_amount(self):
    #     if self.amount > self.fees_id.amount_pending_total:
    #         raise exceptions.ValidationError(
    #             'Amount must be less than pending amount of the financing.')

    @api.model
    def default_get(self, fields):
        res = super(ManualInvoice, self).default_get(fields)
        fees = self.env['agreement.fees'].browse(self.env.context['active_id'])
        res.update({
            'amount_pending': fees.amount_pending_total,
            'fees_id': fees.id,
            'tax_ids': [(6, 0, [t.id for t in fees.tax_ids])]
        })
        return res

    @api.one
    def button_accept(self):
        invoices = self.fees_id.generate_invoice(
            self.amount,
            manual_invoice=True,
            date_invoice=self.date_invoice,
            tax_ids=[t.id for t in self.tax_ids])
        self.fees_id.compute_amortization()
        for invoice in invoices:
            self.fees_id.message_post(
                _('''A manual invoice has created.<br/>
                     <p>&nbsp; &nbsp; • <b>Date</b><span>: %s</span><br/>
                     &nbsp; &nbsp; • <b>Total</b><span>: %s</span></p>
                  ''' % (invoice.date_invoice, invoice.amount_total))
            )
        return {
            'name': _('Invoice'),
            'type': 'ir.actions.act_window',
            'res_model': 'account.invoice',
            'view_type': 'form',
            'view_mode': 'form',
            'res_id': invoices[0].id,
        }
