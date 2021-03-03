# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.

from openerp import models, fields, api, _, exceptions
import datetime
import logging
from openerp.exceptions import ValidationError


_log = logging.getLogger(__name__)


class ModifyFinancing(models.TransientModel):
    _name = 'wiz.modify.financing'
    _description = 'Modify financing.'

    amount_pending = fields.Float(
        string='Amount pending to invoice',
        required=True
    )
    fees_method = fields.Selection(
        selection=[
            ('by_fees', 'by fees'),
            ('by_amount', 'by amount'),
        ],
        string='Fees method',
        default='by_fees'
    )
    fees_number = fields.Integer(
        string='Number of fees',
        required=True
    )
    fees_amount = fields.Float(
        string='Amount',
        required=True
    )
    interest_rate = fields.Float(
        string='Interest rate (%)'
    )
    period_id = fields.Many2one(
        comodel_name='period',
        string='Period',
        required=True
    )
    date_next_invoice = fields.Date(
        'Date next invoice',
        required=True
    )
    payment_financing_id = fields.Many2one(
        comodel_name='agreement.fees',
        string='Payment financing'
    )

    @api.model
    def default_get(self, fields):
        res = super(ModifyFinancing, self).default_get(fields)
        financing = self.env['agreement.fees'].browse(
            self.env.context['active_id'])
        res.update({
            'amount_total': financing.amount_total,
            'amount_pending': financing.amount_pending,
            'interest_rate': financing.interest_rate,
            'fees_method': financing.fees_method,
            'fees_number': financing.fees_number,
            'fees_amount': financing.fees_amount,
            'date_next_invoice': financing.date_next_invoice,
            'period_id': financing.period_id.id,
            'payment_financing_id': self.env.context['active_id'],
        })
        return res

    # Si modifican la cantidad total siempre debe ser a otra mayor (ampliacion
    # de capital financiado)
    @api.constrains('amount_pending')
    @api.one
    def _check_amount_pending(self):
        if self.amount_pending <= 0:
            raise ValidationError('Amount must be greater than 0')

    @api.constrains('interest_rate')
    @api.one
    def _check_interest_rate(self):
        if self.interest_rate < 0:
            raise ValidationError('Interest rate must be greater than 0')

    # Nunca se puede cambiar a menos cuotas de las que ya estan facturadas
    # Minimo = cuotas facturadas + 1 (la ultima)
    @api.constrains('fees_number')
    @api.one
    def _check_fees_number(self):
        if self.fees_method == 'by_fees':
            if self.fees_number <= 0:
                raise ValidationError('Fees number must be greater than 0')

    @api.constrains('fees_amount')
    @api.one
    def _check_fees_amount(self):
        if self.fees_method == 'by_amount':
            if self.fees_amount <= self.financing_id.amount_invoiced:
                raise ValidationError('Fee amount must be greater than %s'
                                      % self.financing_id.amount_invoiced)

    @api.one
    def button_accept(self):
        financing = self.payment_financing_id
        if financing.state != 'financed':
            raise exceptions.Warning(
                _('The financing only can be modified if it is in financed '
                  'state.'))

        data = {}
        if self.date_next_invoice != financing.date_next_invoice:
            init_day_aux = datetime.datetime.strptime(
                self.date_next_invoice, "%Y-%m-%d").date().day
            data.update({'init_day': init_day_aux})

        data.update({
            'amount_total': financing.amount_invoiced + self.amount_pending,
            'interest_rate': self.interest_rate,
            'fees_method': self.fees_method,
            'fees_amount': self.fees_amount,
            'fees_number': self.fees_number,
            'period_id': self.period_id.id,
            'date_next_invoice': self.date_next_invoice,
        })
        financing.write(data)

        financing.compute_amortization()

        return {'type': 'ir.actions.act_window_close'}
