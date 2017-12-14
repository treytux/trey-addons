# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.
from openerp import api, models


class AccountAnalyticLine(models.Model):
    _inherit = 'account.analytic.line'

    @api.one
    def action_remove_invoice_link(self):
        self.write({
            'invoice_id': None})
