# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields


class ProcurementRule(models.Model):
    _inherit = 'procurement.rule'

    procure_method = fields.Selection(
        selection_add=[('mts_mto', 'MTS + MTO')])
