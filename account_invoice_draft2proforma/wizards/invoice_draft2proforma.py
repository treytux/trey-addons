# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.

from openerp import models, api, _, exceptions
import logging

_log = logging.getLogger(__name__)


class InvoiceDraft2proforma(models.TransientModel):
    _name = 'wiz.invoice_draft2proforma'
    _description = 'Change state of the invoices selected.'

    @api.one
    def button_accept(self):
        # Comprobar que todas las facturas seleccionadas estan en estado
        # borrador
        invoices = self.env['account.invoice'].browse(
            self.env.context['active_ids'])

        for invoice in invoices:
            if invoice.state != 'draft':
                raise exceptions.Warning(
                    _('All invoices selected must be in \'draft\' state.')
                )
        # Cambiar el estado de cada factura
        for invoice in invoices:
            invoice.signal_workflow('invoice_proforma2')
        return {'type': 'ir.actions.act_window_close'}
