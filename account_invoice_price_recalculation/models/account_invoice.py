# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, api


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    @api.multi
    def recalculate_prices(self):
        for invoice in self:
            if not invoice.invoice_line:
                return
            for line in invoice.invoice_line:
                res = line.product_id_change(
                    product=line.product_id.id,
                    uom_id=False,
                    qty=line.quantity,
                    name=line.name,
                    type=invoice.type,
                    partner_id=invoice.partner_id.id,
                    fposition_id=invoice.fiscal_position.id,
                    currency_id=invoice.currency_id.id)
                line.write(res['value'])
