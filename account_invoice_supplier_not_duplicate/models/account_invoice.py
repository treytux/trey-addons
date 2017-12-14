# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.
from openerp import models, api, exceptions, _


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    @api.one
    def action_move_create(self):
        if self.type == 'in_invoice' and self.reference_type:
            invs = self.search([
                ('id', '!=', self.id),
                ('type', '=', self.type),
                ('partner_id', '=', self.partner_id.id),
                ('supplier_invoice_number', '=', self.supplier_invoice_number)
            ], limit=1)
            if invs:
                raise exceptions.Warning(
                    _('The supplier invoice "%s" already exists for '
                      'supplier %s') % (
                        self.supplier_invoice_number, self.partner_id.name))
        super(AccountInvoice, self).action_move_create()
