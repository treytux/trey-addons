# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import api, fields, models


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    invoiced = fields.Boolean(
        compute='_compute_invoiced')

    @api.one
    @api.depends('invoice_lines.invoice_id.state')
    def _compute_invoiced(self):
        self.invoiced = (
            self.invoice_lines and any(
                iline.invoice_id.state != 'cancel'
                for iline in self.invoice_lines))
