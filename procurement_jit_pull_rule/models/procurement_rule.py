# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields


class ProcurementRule(models.Model):
    _inherit = 'procurement.rule'

    active_jit = fields.Boolean(
        string='Activate jit',
        help='Activates the just in time computation in the procurement order '
        'for this rule, so that the procurement orders related to it will be '
        'executed automatically.')
