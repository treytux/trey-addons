# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, api, fields, _
from openerp.exceptions import Warning


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    force_number = fields.Char(
        string='Force number',
    )

    def _force_number(self, vals):
        if 'invoice_number' in vals or 'number' in vals:
            return
        if vals.get('force_number'):
            sales = self.search([
                '|', ('number', '=', vals['force_number']),
                ('invoice_number', '=', vals['force_number'])
            ])
            if sales:
                raise Warning(
                    _('Account invoice number %s already exist!')
                    % vals['force_number'])
            vals['invoice_number'] = vals['force_number']
            vals['number'] = vals['force_number']

    @api.multi
    def action_number(self):
        for invoice in self:
            invoice.force_number = False
        return super(AccountInvoice, self).action_number()

    @api.model
    def create(self, vals):
        self._force_number(vals)
        return super(AccountInvoice, self).create(vals)

    @api.multi
    def write(self, vals):
        self._force_number(vals)
        return super(AccountInvoice, self).write(vals)
