# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields


class EduAcademicTraining(models.Model):
    _name = 'edu.academic.training'
    _description = 'Academic Training'

    name = fields.Char(
        string='Name',
        required=True)
