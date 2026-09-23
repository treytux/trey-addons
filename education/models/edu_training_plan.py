###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class EduTrainingPlan(models.Model):
    _name = 'edu.training.plan'
    _description = 'Training Plan'
    _inherit = ['mail.thread']

    name = fields.Char(
        string='Name',
        required=True,
    )
    short_name = fields.Char(
        string='Short name',
    )
    description = fields.Text(
        string='Description',
    )
    active = fields.Boolean(
        string='Active',
        default=True,
    )
    start_date = fields.Date(
        string='Start date',
        required=True,
    )
    end_date = fields.Date(
        string='End date',
        required=True,
    )
    state = fields.Selection(
        string='State',
        selection=[
            ('in_progress', 'In progress'),
            ('closed', 'Closed'),
        ],
        required=True,
        default='in_progress',
    )
    subject_ids = fields.One2many(
        comodel_name='edu.subject',
        compute='_compute_subjects',
        string='Subjects',
    )
    line_ids = fields.One2many(
        comodel_name='edu.training.plan.line',
        inverse_name='training_plan_id',
        string='Lines',
    )
    classroom_ids = fields.One2many(
        comodel_name='edu.training.plan.classroom',
        inverse_name='training_plan_id',
        string='Classroom',
    )
    typology_id = fields.Many2one(
        comodel_name='edu.training.plan.typology',
        string='Typology',
    )
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.company,
    )
    user_id = fields.Many2one(
        comodel_name='res.users',
        string='Responsible',
    )

    @api.depends('line_ids')
    def _compute_subjects(self):
        for training_plan in self:
            subject_ids = list(set([
                ln.subject_id.id for ln in training_plan.line_ids]))
            training_plan.subject_ids = [(6, 0, subject_ids)]

    @api.constrains('start_date', 'end_date')
    def _check_dates(self):
        for training_plan in self:
            if not training_plan.end_date or not training_plan.start_date:
                continue
            if training_plan.end_date < training_plan.start_date:
                raise ValidationError(
                    _('Start date cannot be later than the end date.'))
