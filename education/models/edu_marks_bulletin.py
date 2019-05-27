# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields, api
from datetime import datetime


class EduMarksBulletin(models.Model):
    _name = 'edu.marks.bulletin'
    _description = 'Marks Bulletin'

    name = fields.Many2one(
        comodel_name='res.partner',
        required=True,
        string='Student')
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.user.company_id)
    training_plan_id = fields.Many2one(
        comodel_name='edu.training.plan',
        string='Training Plan',
        required=True)
    classroom_id = fields.Many2one(
        comodel_name='edu.training.plan.classroom',
        string='Classroom',
        domain="[('training_plan_id','=',training_plan_id)]",
        copy=False)
    year = fields.Char(
        string='Session',
        compute='_compute_year')
    tutor_id = fields.Many2one(
        comodel_name='res.partner',
        relation='edu_enrollment2res_partner_rel',
        string='Tutor',
        domain="[('is_tutor', '=', True)]")
    evaluation_line_ids = fields.One2many(
        comodel_name='edu.evaluation.line',
        inverse_name='enrollment_id',
        string='Evaluation Lines')
    promote = fields.Selection(
        selection=[
            ('Promote', 'Promote'),
            ('Not_promote', 'Not promote')
        ],
        string='Promotion')
    observations = fields.Text(
        string='Comments')

    @api.one
    @api.depends('training_plan_id')
    def _compute_year(self):
        if self.training_plan_id:
            enroll_obj = self.env['edu.training.plan'].browse(
                self.training_plan_id.id)
            start_date = datetime.strptime(enroll_obj.start_date, '%Y-%m-%d')
            end_date = datetime.strptime(enroll_obj.end_date, '%Y-%m-%d')
            self.year = str(start_date.year) + '-' + str(end_date.year)
