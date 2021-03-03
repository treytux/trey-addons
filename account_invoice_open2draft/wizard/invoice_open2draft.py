# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, api, _, exceptions
import logging

_log = logging.getLogger(__name__)


class InvoiceOpen2Draft(models.TransientModel):
    _name = 'wiz.invoice_open2draft'
    _description = 'Change state of the invoices selected'

    @api.one
    def button_accept(self):
        invoices = self.env['account.invoice'].browse(
            self.env.context['active_ids'])
        for invoice in invoices:
            if invoice.state != 'open':
                raise exceptions.Warning(
                    _('All invoices selected must be in open state.')
                )
        for invoice in invoices:
            invoice.action_cancel()
            invoice.action_cancel_draft()
        return {'type': 'ir.actions.act_window_close'}
