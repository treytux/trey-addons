# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields


class PosConfig(models.Model):
    _inherit = 'pos.config'

    same_sign = fields.Boolean(
        string='Check if all lines have same sign',
        help='Before to pay check if all lines have the same sign positive '
             'or negative')
