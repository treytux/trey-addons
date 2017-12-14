# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, api, fields


class ResPartner(models.Model):
    _inherit = 'res.partner'

    amount_pending = fields.Float(
        compute='_compute_pending',
        string='Amount Pending',
        help='Calculate Amount Pending in Invoice.')
    credit_total = fields.Float(
        compute='_compute_pending',
        string='Total credit',
        help='Credit + Amount pending.')

    @api.one
    def _compute_pending(self):
        if self.customer and self.is_company:
            invoices = self.env['account.invoice'].search([
                ('partner_id', '=', self.id),
                ('state', '=', 'pending')])
            self.amount_pending = sum(
                [(i.type == 'out_invoice' and
                  i.amount_total or (i.amount_total * -1)) for i in invoices])
            self.credit_total = self.amount_pending + self.credit
