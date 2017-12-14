# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.
from openerp import models, api, _


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    @api.multi
    def action_print_options_account_invoice(self):
        wiz = self.env['wiz.print.options.account.invoice'].create({})
        return {
            'name': _('Print'),
            'type': 'ir.actions.act_window',
            'res_model': 'wiz.print.options.account.invoice',
            'view_type': 'form',
            'view_mode': 'form',
            'res_id': wiz.id,
            'target': 'new'}
