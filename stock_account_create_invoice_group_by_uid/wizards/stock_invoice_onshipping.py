# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields, api


class StockInvoiceOnShipping(models.TransientModel):
    _inherit = 'stock.invoice.onshipping'

    group_by_user = fields.Boolean(
        string='Group by user',
        default=True,
        help="Assigns the user who is launching this wizard as responsible "
        "for the generated invoices. It must be used together with "
        "'Group by company' so that an invoice is not generated per user.")

    @api.multi
    def create_invoice(self):
        group_by_user = self.group_by_user
        return super(StockInvoiceOnShipping, self.with_context(
            group_by_user=group_by_user)).create_invoice()
