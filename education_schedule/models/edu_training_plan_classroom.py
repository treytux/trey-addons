# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields


class EduTrainingPlanClassroom(models.Model):
    _inherit = 'edu.training.plan.classroom'
    time_slot_ids = fields.Many2many(
        comodel_name='edu.time.slot',
        relation='classroom_time_slot_rel',
        column1='classroom_id',
        column2='time_slot_id')
