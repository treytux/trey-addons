# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, api


class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'

    @api.model
    def _update_sii_tax_line(self, tax_dict, tax_line):
        super(AccountInvoiceLine, self)._update_sii_tax_line(
            tax_dict=tax_dict, tax_line=tax_line)
        if tax_line.child_depend:
            tax_type = abs(tax_line.child_ids.filtered('amount')[:1].amount)
        else:
            tax_type = abs(tax_line.amount)

        tax_dict[tax_type]['TipoImpositivo'] = "{:.2f}".format(tax_type * 100)
        return True
