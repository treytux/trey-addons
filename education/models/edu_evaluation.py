# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields


class EduEvaluation(models.Model):
    _name = 'edu.evaluation'
    _description = 'Evaluation'

    name = fields.Char(
        string='Name')
    sequence = fields.Integer(
        string='Sequence')
