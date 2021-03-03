# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, api, exceptions, _


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    @api.multi
    def invoice_validate(self):
        res = super(AccountInvoice, self).invoice_validate()
        purchase_conf = self.env['purchase.config.settings'].default_get([])
        if purchase_conf['inv_number_unique']:
            self.action_validate_invoice_number()
        if purchase_conf['inv_ref_unique']:
            self.action_validate_invoice_ref()
        return res

    @api.multi
    def action_validate_invoice_number(self):
        for inv in self:
            if inv.supplier_invoice_number:
                invoice_ids = self.env['account.invoice'].search([
                    ('supplier_invoice_number', '!=', False),
                    ('company_id', '=', inv.company_id.id),
                    ('type', '=', inv.type),
                ])
                invoice_duplicate_ids = []
                for invoice_r in invoice_ids:
                    if inv.id != invoice_r.id and inv.partner_id.id == \
                            invoice_r.partner_id.id and \
                            inv.supplier_invoice_number.upper() == \
                            invoice_r.supplier_invoice_number.upper() and \
                            invoice_r.state != 'cancel':
                        invoice_duplicate_ids.append(invoice_r.id)
                if invoice_duplicate_ids:
                    raise exceptions.Warning(
                        _('Validation error!'),
                        _('It is not possible to validate the invoice, '
                          'supplier invoice number duplicated.')
                    )
        return True

    @api.multi
    def action_validate_invoice_ref(self):
        for inv in self:
            if inv.reference:
                invoice_ids = self.env['account.invoice'].search([
                    ('reference', '!=', False),
                    ('company_id', '=', inv.company_id.id),
                    ('type', '=', inv.type),
                ])
                invoice_duplicate_ids = []
                for invoice_r in invoice_ids:
                    if inv.id != invoice_r.id and inv.partner_id.id == \
                            invoice_r.partner_id.id and \
                            inv.reference.upper() == \
                            invoice_r.reference.upper() and \
                            invoice_r.state != 'cancel':
                        invoice_duplicate_ids.append(invoice_r.id)
                if invoice_duplicate_ids:
                    raise exceptions.Warning(
                        _('Validation error!'),
                        _('It is not possible to validate the invoice, '
                          'paiment reference duplicated.')
                    )
        return True
