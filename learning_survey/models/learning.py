# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.
from openerp import models, fields, api


class LearningSubscription(models.Model):
    _inherit = 'learning.subscription'

    @api.one
    @api.depends('user_input_ids')
    def calculate_approved(self):
        if self.user_input_ids:
            for user_input in self.user_input_ids:
                self.approved = bool(user_input.approved)

    @api.one
    @api.depends('user_input_ids')
    def calculate_try_exam(self):
        if not self.approved and self.remaining_days > 0 and \
           self.exam_attempts >= 0:
            if self.user_input_ids:
                for user_input in self.user_input_ids:
                    if user_input.state != 'done' or not user_input.approved:
                        self.try_exam = True
                        break
            self.try_exam = True

    user_input_ids = fields.One2many(
        comodel_name='survey.user_input',
        inverse_name='subscription_id',
        string='Exams',
        required=False)
    approved = fields.Boolean(
        string='Approved',
        compute='calculate_approved',
        # store=True)
        store=False)
    try_exam = fields.Boolean(
        string='Try Exam',
        compute='calculate_try_exam')
