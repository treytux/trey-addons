# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import fields, models, api


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    invoice_unpaid = fields.Float(
        string='Balance',
        compute='_compute_unpaid_invoices')

    @api.one
    def _compute_unpaid_invoices(self):
        self.invoice_unpaid = sum([i.residual for i in self.invoice_ids])
