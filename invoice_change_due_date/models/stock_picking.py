# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields, api


class stock_picking(models.Model):
    _inherit = 'stock.picking'

    date_value = fields.Date(
        string='Value date',
        states={'draft': [('readonly', False)]},
        help='Value date to compute due date on sale order invoice.')

    @api.model
    def _prepare_invoice(self, picking, partner, inv_type, journal_id):
        invoice_vals = super(stock_picking, self)._prepare_invoice(
            picking, partner, inv_type, journal_id)
        if picking.date_value:
            invoice_vals['date_value'] = picking.date_value
        elif (not picking.date_value and picking.sale_id and
              picking.sale_id.date_value):
            invoice_vals['date_value'] = picking.sale_id.date_value
        return invoice_vals

    @api.multi
    def action_invoice_create(self, journal_id, group, type):
        invoice_ids = super(stock_picking, self).action_invoice_create(
            journal_id, group, type)
        for invoice in self.env['account.invoice'].browse(invoice_ids):
            if self.date_value:
                invoice.date_value = self.date_value
            elif (not self.date_value and
                  self.sale_id and self.sale_id.date_value):
                invoice.date_value = self.sale_id.date_value
            invoice.onchange_payment_term_date_invoice(
                invoice.payment_term.id, invoice.date_value)
        return invoice_ids
