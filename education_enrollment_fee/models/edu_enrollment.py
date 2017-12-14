# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields


class EduEnrollment(models.Model):
    _inherit = 'edu.enrollment'

    fee_generator_id = fields.Many2one(
        comodel_name='fee.generator',
        string='Fees',
        copy=False)
