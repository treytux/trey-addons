# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.
from openerp import models, api, exceptions, fields, _


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    @api.multi
    def invoice_validate(self):
        if not self.partner_id.vat and self.journal_id.require_vat:
            if not self.fiscal_position:
                raise exceptions.Warning(
                    _("You can not validate the invoice, because the fiscal "
                      "position no set"))
            else:
                position = self.env.ref('l10n_es.fp_extra')
                if position.id != self.fiscal_position.id:
                    raise exceptions.Warning(
                        _("You can not validate the invoice, because the "
                          "client/supplier has no vat."))
        super(AccountInvoice, self).invoice_validate()


class Journal(models.Model):
    _inherit = 'account.journal'

    require_vat = fields.Boolean(string='Require VAT when open invoice')
