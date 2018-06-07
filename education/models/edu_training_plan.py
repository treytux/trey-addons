# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields, api


class EduTrainingPlan(models.Model):
    _name = 'edu.training.plan'
    _description = 'Training Plan'
    _inherit = ['mail.thread']

    name = fields.Char(
        string='Name',
        required=True)
    short_name = fields.Char(
        string='Short name')
    description = fields.Text(
        string='Description')
    active = fields.Boolean(
        string='Active',
        default=True,
        track_visibility='onchange')
    start_date = fields.Date(
        string='Start date',
        required=True)
    end_date = fields.Date(
        string='End date')
    subject_ids = fields.One2many(
        comodel_name='edu.subject',
        compute='_compute_subjects',
        string='Subjects')
    line_ids = fields.One2many(
        comodel_name='edu.training.plan.line',
        inverse_name='training_plan_id',
        string='Lines')
    classroom_ids = fields.One2many(
        comodel_name='edu.training.plan.classroom',
        inverse_name='training_plan_id',
        string='Classroom')
    typology_id = fields.Many2one(
        comodel_name='edu.training.plan.typology',
        string='Typology')
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.user.company_id)

    @api.one
    @api.depends('line_ids')
    def _compute_subjects(self):
        subject_ids = list(set([l.subject_id.id for l in self.line_ids]))
        self.subject_ids = [(6, 0, subject_ids)]
