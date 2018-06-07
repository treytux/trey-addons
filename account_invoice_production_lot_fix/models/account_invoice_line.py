# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, api


class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'

    @api.one
    def load_line_lots(self):
        super(AccountInvoiceLine, self).load_line_lots()
        if not self.prod_lot_ids:
            self.lot_formatted_note = u''
