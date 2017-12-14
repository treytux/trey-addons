# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.
from openerp import models, api, exceptions, _, fields


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    @api.multi
    def action_number(self):
        def replace(code):
            if not code:
                return ''
            replaces = {
                '%(year)s': 4,
                '%(sec)s': 2,
                '%(weekday)s': 1,
                '%(month)s': 2,
                '%(h12)s': 2,
                '%(y)s': 2,
                '%(doy)s': 3,
                '%(day)s': 2,
                '%(woy)s': 2,
                '%(h24)s': 2,
                '%(min)s': 2
            }
            for k, v in replaces.iteritems():
                code = code.replace(k, '_'*v)
            return code

        re = super(AccountInvoice, self).action_number()
        for invoice in self:
            if not invoice.journal_id.sequential_date:
                continue
            if invoice.type == 'in_invoice' or invoice.type == 'in_refund':
                continue
            sequence = self.journal_id.invoice_sequence_id
            for line in sequence.fiscal_ids:
                if line.fiscalyear_id.id == invoice.period_id.fiscalyear_id.id:
                    sequence = line.sequence_id
            prefix = replace(sequence.prefix)
            suffix = replace(sequence.suffix)
            prev_num = invoice.number[len(prefix):]
            prev_num = suffix and prev_num[:len(suffix) * -1] or prev_num
            prev_num = str(int(prev_num) - 1).zfill(sequence.padding or 0)
            res = self.search([
                ('type', '=', invoice.type),
                ('date_invoice', '>', invoice.date_invoice),
                ('number', 'like', prefix + prev_num + suffix),
                ('journal_id', '=', invoice.journal_id.id)])
            if res:
                raise exceptions.Warning(
                    _('Date Inconsistency'),
                    _('Cannot create invoice! Post the invoice with a '
                      'greater date. Last Invoice: %s , Date: %s') % (
                        res[0].number, res[0].date_invoice))

        return re


class Journal(models.Model):
    _inherit = 'account.journal'

    sequential_date = fields.Boolean(string='Sequential date')
