# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.
from openerp import models, api


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    @api.multi
    def unlink(self):
        for invoice in self:
            for picking in invoice.picking_ids:
                picking.invoice_state = '2binvoiced'
                for move in picking.move_lines:
                    move.invoice_state = '2binvoiced'
        res = super(AccountInvoice, self).unlink()
        return res
