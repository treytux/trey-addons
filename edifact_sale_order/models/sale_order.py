# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields


class SaleOrder(models.Model):
    _inherit = "sale.order"

    edi_doc_id = fields.Many2one(
        comodel_name='edifact.document',
        string='Import')
