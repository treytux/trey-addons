# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields, api, exceptions, _


class WizInvoiceTaxChange(models.TransientModel):
    _name = 'wiz.invoice.tax.change'
    _description = 'Wizard invoice change tax'

    name = fields.Char(
        string='Empty')
    tax_ids = fields.Many2many(
        comodel_name='account.tax',
        relation='invoice_change_account_tax_rel',
        column1='change_tax_id',
        column2='tax_id')

    @api.multi
    def button_accept(self):
        invoice_ids = self.env.context.get('active_ids', [])
        for invoice in self.env['account.invoice'].browse(invoice_ids):
            if invoice.state not in ['draft']:
                raise exceptions.Warning(_(
                    'The invoice state must be \'Draft\''))
            for line in invoice.invoice_line:
                for old_tax in line.invoice_line_tax_id:
                    line.write({'invoice_line_tax_id': [(3, old_tax.id)]})
                for new_tax in self.tax_ids:
                    line.write({'invoice_line_tax_id': [(4, new_tax.id)]})
            invoice.button_reset_taxes()
        return {'type': 'ir.actions.act_window_close'}
