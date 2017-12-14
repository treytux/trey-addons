# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.

from openerp import models, api, exceptions, _


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    @api.multi
    def invoice_validate(self):
        self.action_validate_ref_invoice()
        super(AccountInvoice, self).invoice_validate()

    @api.multi
    def action_validate_ref_invoice(self):
        invoice_obj = self.env['account.invoice']
        invoice_duplicate_ids = []
        invoice_ids = invoice_obj.search([
            ('supplier_invoice_number', '<>', None),
            ('company_id', '=', self.company_id.id),
            ('type', '=', self.type)]
        )
        if self.supplier_invoice_number:
            for invoice_r in invoice_ids:
                if self.id != invoice_r.id and self.partner_id.id == \
                        invoice_r.partner_id.id and \
                        self.supplier_invoice_number.upper() == \
                        invoice_r.supplier_invoice_number.upper() and \
                        invoice_r.state != 'cancel':
                    invoice_duplicate_ids.append(invoice_r.id)
        if invoice_duplicate_ids:
            raise exceptions.Warning(
                _('Invalid Action!'),
                _('Error you can not validate the invoice with supplier '
                  'invoice number duplicated.')
            )
        return True
