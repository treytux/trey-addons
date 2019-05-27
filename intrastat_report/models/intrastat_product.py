# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields


class L10nEsReportIntrastatProduct(models.Model):
    _inherit = 'l10n.es.report.intrastat.product'

    invoice_id = fields.Many2one(
        comodel_name='account.invoice',
        string='Invoice')
