# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.
from openerp import models, api


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    @api.multi
    def onchange_partner_id(
            self, type, partner_id, date_invoice=False, payment_term=False,
            partner_bank_id=False, company_id=False):
        res = super(AccountInvoice, self).onchange_partner_id(
            type=type, partner_id=partner_id, date_invoice=date_invoice,
            payment_term=payment_term, partner_bank_id=partner_bank_id,
            company_id=company_id)
        if partner_id and type in ('out_invoice', 'out_refund'):
            partner = self.env['res.partner'].browse(partner_id)
            for bank in partner.bank_ids:
                active_mandates = bank.mandate_ids.filtered(
                    lambda x: x.state == 'valid')
                if active_mandates:
                    res['value']['mandate_id'] = active_mandates[0].id
        return res
