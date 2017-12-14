# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.

from openerp import models, fields, api, exceptions, _
from datetime import datetime
import logging

_log = logging.getLogger(__name__)


class LearningResource(models.Model):
    _name = 'learning.resource'
    _description = 'Resources'

    name = fields.Char(
        string='Name',
        required=True)
    description = fields.Html(
        string='Description')
    total_hours = fields.Float(
        string='Time',
        digits=(16, 2),
        default=0,
        help='Total estimated time for read or visualization in h')
    attachment_id = fields.Many2one(
        comodel_name='ir.attachment',
        string='Attachment')


class LearningExam(models.Model):
    _name = 'learning.exam'
    _description = 'Exams'

    @api.one
    def _number_questions(self):
        if self.survey_id:
            self.number_questions = len(self.survey_id.page_ids)

    name = fields.Char(
        string='Name',
        required=False,
        related='survey_id.title')
    description = fields.Html(
        string='Description')
    survey_id = fields.Many2one(
        comodel_name='survey.survey',
        string='Survey Form',
        required=True,
        help='Survey form related for this exam')
    exam_attempts = fields.Integer(
        string="Exam Attempts",
        required=False)
    min_score = fields.Float(
        string="Minimum Score",
        required=True)
    number_questions = fields.Integer(
        string='Number Questions',
        required=True,
        default=_number_questions)

    @api.constrains('number_questions')
    @api.one
    def _check_number_questions(self):
        if self.number_questions > len(self.survey_id.page_ids):
            raise exceptions.ValidationError(
                _('Number of Question out of range.'))

    @api.onchange('survey_id')
    def onchange_survey_id(self):
        if self.survey_id:
            self.name = self.survey_id.title
            self.number_questions = len(self.survey_id.page_ids)


class LearningCategory(models.Model):

    @api.multi
    def _name_get_fnc(self, prop, unknow_none):
        res = self.name_get()
        return dict(res)

    _name = 'learning.category'
    _description = 'Learning Category'

    name = fields.Char(
        string='Name',
        required=True,
        translate=True,
        select=True)
    parent_id = fields.Many2one(
        comodel_name='learning.category',
        string='Parent Category',
        select=True,
        ondelete='cascade')
    child_id = fields.One2many(
        comodel_name='learning.category',
        inverse_name='parent_id',
        string='Child Categories')
    sequence = fields.Integer(
        string='Sequence',
        select=True,
        help='Gives the sequence order when displaying a training list ')
    parent_left = fields.Integer(
        string='Left Parent',
        select=1)
    parent_right = fields.Integer(
        string='Right Parent',
        select=1)

    _parent_name = 'parent_id'
    _parent_store = True
    _parent_order = 'sequence, name'
    _order = 'parent_left'


class LearningTraining(models.Model):
    _name = 'learning.training'
    _description = 'Training'

    name = fields.Char(
        string='Name',
        required=True)
    description = fields.Html(
        string='Description',
        copy=True)
    target = fields.Html(
        string='Targets',
        copy=True)
    template_id = fields.Many2one(
        comodel_name='product.template',
        string='Product',
        required=True,
        domain=[('subscription_ok', '=', True)],
        copy=True)
    category_id = fields.Many2one(
        comodel_name='learning.category',
        string='Category',
        required=True,
        copy=True)
    lesson_line = fields.One2many(
        comodel_name='learning.training.lesson',
        inverse_name='training_id',
        string='Lesson',
        copy=True)
    exam_id = fields.Many2one(
        comodel_name='learning.exam',
        string="Exam",
        required=False)
    duration_type = fields.Selection(
        string='Duration Type',
        selection=[
            ('days', 'Days'),
            ('weeks', 'Weeks'),
            ('months', 'Months'),
            ('years', 'Years')],
        default='months')
    duration = fields.Integer(
        string='Duration',
        default=1,
        required=True)
    url = fields.Char(
        string='URL',
        help='Url for Vimeo Video')


class LearningTrainingLesson(models.Model):
    _name = 'learning.training.lesson'
    _description = 'Training Lesson'

    training_id = fields.Many2one(
        comodel_name='learning.training',
        string='Training',
        required=True,
        ondelete='cascade')
    sequence = fields.Integer(
        string='Sequence',
        required=True,
        default='10')
    name = fields.Char(
        string='Name')
    description = fields.Html(
        string='Description')
    url = fields.Char(
        string='URL',
        help='Url for Vimeo Video')
    resource_line = fields.One2many(
        comodel_name='learning.training.lesson.resource',
        inverse_name='lesson_id',
        string='Resources',
        copy=True)
    estimated_time = fields.Float(
        string='Estimated Time',
        digits=(16, 2),
        default=0,
        help='Estimated time in h')
    parent_id = fields.Many2one(
        comodel_name='learning.training.lesson',
        string='Parent Lesson',
        select=True,
        ondelete='cascade')
    child_id = fields.One2many(
        comodel_name='learning.training.lesson',
        inverse_name='parent_id',
        string='Child Categories')
    parent_left = fields.Integer(
        string='Left Parent',
        select=1)
    parent_right = fields.Integer(
        string='Right Parent',
        select=1)

    _parent_name = 'parent_id'
    _parent_store = True
    _parent_order = 'sequence, name'
    _order = 'parent_left'


class LearningTrainingLessonResource(models.Model):
    _name = 'learning.training.lesson.resource'
    _description = 'Training Lesson Resource'

    sequence = fields.Integer(
        string='Sequence',
        required=True,
        default='10')
    lesson_id = fields.Many2one(
        comodel_name='learning.training.lesson',
        string='Lesson',
        required=True,
        ondelete='cascade')
    resource_id = fields.Many2one(
        comodel_name='learning.resource',
        string='Resource',
        required=True)


class LearningSubscription(models.Model):
    _name = 'learning.subscription'
    _description = 'Learning Subscription'

    @api.one
    @api.depends()
    def _remaining_days(self):
        date_format = '%Y-%m-%d'
        date_now = datetime.now().strftime('%Y-%m-%d')
        date_now = datetime.strptime(date_now, date_format)
        date_end = datetime.strptime(self.date_end, date_format)
        self.remaining_days = (date_end - date_now).days

    state = fields.Selection(
        string='State',
        selection=[('draft', 'Draft'), ('progress', 'Progress'),
                   ('locked', 'Locked'), ('done', 'Done')],
        default='draft')
    name = fields.Char(
        string='Name')
    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Customer',
        domain=[('customer', '=', True)])
    order_id = fields.Many2one(
        comodel_name='sale.order',
        string='Sale Order')
    invoice_id = fields.Many2one(
        comodel_name='account.invoice',
        string='Invoice')
    date_init = fields.Date(
        string='Start',
        required=True,
        default=fields.Date.context_today,
        readonly=True)
    date_end = fields.Date(
        string='End',
        required=True,
        default=fields.Date.context_today,
        readonly=True)
    remaining_days = fields.Integer(
        string='Remaining Days',
        store=False,
        compute=_remaining_days)
    training_id = fields.Many2one(
        comodel_name='learning.training',
        string='Training')
    note = fields.Html(
        string='Notes')
    color = fields.Integer(
        string='Color Index')
    exam_attempts = fields.Integer(
        string='Exam Attempts',
        required=False)
