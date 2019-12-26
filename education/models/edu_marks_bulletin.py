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
    enrollment_id = fields.Many2one(
        comodel_name='edu.enrollment',
        string='Enrollment',
        required=True,
        domain="[('student_id','=',name)]")
    classroom_id = fields.Many2one(
        comodel_name='edu.training.plan.classroom',
        string='Classroom')
    year = fields.Char(
        string='Session',
        compute='_compute_year')
    tutor_ids = fields.Many2many(
        comodel_name='res.partner',
        relation='edu_marks_bulletin2res_partner_rel',
        string='Tutors',
        column1='bulletin_id',
        column2='partner_id',
        compute='_compute_tutors')
    evaluation_line_ids = fields.One2many(
        comodel_name='edu.evaluation.line',
        inverse_name='bulletin_id',
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
    @api.depends('enrollment_id')
    def _compute_year(self):
        training = self.env['edu.training.plan'].browse(
            self.enrollment_id.training_plan_id.id)
        if training and training.start_date and training.end_date:
            start_date = datetime.strptime(training.start_date, '%Y-%m-%d')
            end_date = datetime.strptime(training.end_date, '%Y-%m-%d')
            self.year = str(start_date.year) + '-' + str(end_date.year)

    @api.onchange('enrollment_id')
    def _compute_tutors(self):
        self.tutor_ids = self.enrollment_id.tutor_ids

    @api.multi
    def button_fill_subjects(self):
        view = self.env.ref('education.fill_subjects_wizard')
        return {
            'model': self.id,
            'res_model': 'edu.wizard.fill.subjects',
            'target': 'new',
            'type': 'ir.actions.act_window',
            'view_id': view.id,
            'view_mode': 'form',
            'view_type': 'form'}
