# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.
from openerp import models, api
import logging

_log = logging.getLogger(__name__)


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    @api.multi
    def invoice_validate(self):
        """ ******************************************************
            Sobreescritura del metodo de confirmacion de factura
            para asignar la factura a la subscripcion.
            ******************************************************
        """
        res = super(AccountInvoice, self).invoice_validate()
        _log.info("invoice_validate %s", self._ids)
        for invoice in self:
            for line in invoice.invoice_line:
                if line.product_id.product_tmpl_id.subscription_ok:
                    trainings = self.env['learning.training'].search_read(
                        [('template_id', '=',
                            line.product_id.product_tmpl_id.id)], ['id'])
                    if trainings:
                        training_ids = []
                        for t in trainings:
                            training_ids.append(t['id'])
                        subscription = self.env[
                            'learning.subscription'].search([
                                ('partner_id', '=', self.partner_id.id),
                                ('training_id', 'in', training_ids)
                            ])
                        if subscription:
                            subscription.invoice_id = invoice.id

        return res
