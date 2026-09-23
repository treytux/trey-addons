###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class EduMarksBulletin(models.Model):
    _name = 'edu.marks.bulletin'
    _description = 'Marks Bulletin'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Many2one(
        comodel_name='res.partner',
        required=True,
        string='Student',
    )
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.user.company_id,
    )
    enrollment_id = fields.Many2one(
        comodel_name='edu.enrollment',
        string='Enrollment',
        required=True,
        domain="[('student_id','=',name)]",
    )
    classroom_id = fields.Many2one(
        comodel_name='edu.training.plan.classroom',
        string='Classroom',
        related='enrollment_id.classroom_id',
    )
    year = fields.Char(
        string='Session',
        compute='_compute_year',
    )
    tutor_ids = fields.Many2many(
        comodel_name='res.partner',
        relation='edu_marks_bulletin2res_partner_rel',
        string='Tutors',
        column1='bulletin_id',
        column2='partner_id',
        compute='_compute_tutors',
    )
    evaluation_line_ids = fields.One2many(
        comodel_name='edu.evaluation.line',
        inverse_name='bulletin_id',
        string='Evaluation Lines',
    )
    promote = fields.Selection(
        selection=[
            ('promote', 'Promote'),
            ('not_promote', 'Not promote')
        ],
        string='Promotion',
    )
    observations = fields.Text(
        string='Comments',
    )
    has_pending_evaluation = fields.Boolean(
        compute='_compute_has_pending_evaluation',
        string='Has pending evaluation',
        store=True,
    )

    @api.depends('evaluation_line_ids.mark')
    def _compute_has_pending_evaluation(self):
        for bulletin in self:
            bulletin.has_pending_evaluation = any([
                not line.mark
                for line in bulletin.evaluation_line_ids])

    @api.depends('enrollment_id')
    def _compute_year(self):
        for bulletin in self:
            training = self.env['edu.training.plan'].browse(
                bulletin.enrollment_id.training_plan_id.id)
            if training and training.start_date and training.end_date:
                bulletin.year = (
                    training.start_date.strftime('%Y')
                    + '-'
                    + training.end_date.strftime('%Y'))

    @api.depends('enrollment_id')
    def _compute_tutors(self):
        for bulleting in self:
            bulleting.tutor_ids = [
                (6, 0, bulleting.enrollment_id.tutor_ids.ids),
            ]

    def button_fill_subjects(self):
        self.ensure_one()
        view = self.env.ref('education.fill_subjects_wizard')
        return {
            'model': self.id,
            'res_model': 'edu.wizard.fill.subjects',
            'target': 'new',
            'type': 'ir.actions.act_window',
            'view_id': view.id,
            'view_mode': 'form',
            'view_type': 'form',
        }
