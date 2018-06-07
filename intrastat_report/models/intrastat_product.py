# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields, api


class L10nEsReportIntrastatProduct(models.Model):
    _inherit = 'l10n.es.report.intrastat.product'

    invoice_id = fields.Many2one(
        comodel_name='account.invoice',
        string='Invoice')

    @api.multi
    def create_intrastat_product_lines(self, invoice, parent_values):
        res = super(
            L10nEsReportIntrastatProduct, self).create_intrastat_product_lines(
                invoice, parent_values)
        for line in self.intrastat_line_ids:
            line.invoice_id = invoice.id
        return res
