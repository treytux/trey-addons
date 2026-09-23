###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, api, exceptions, fields, models


class EduTrainingPlanLine(models.Model):
    _name = 'edu.training.plan.line'
    _description = 'Training plan line'
    _inherit = ['mail.thread']

    name = fields.Char(
        compute='_compute_name',
        string='Name',
        states={
            'active': [('readonly', True)],
            'ended': [('readonly', True)],
            'cancelled': [('readonly', True)],
        },
        required=True,
    )
    state = fields.Selection(
        selection=[
            ('draft', 'Draft'),
            ('active', 'Active'),
            ('ended', 'Ended'),
            ('cancelled', 'Cancelled'),
        ],
        string='State',
        default='draft',
    )
    training_plan_id = fields.Many2one(
        comodel_name='edu.training.plan',
        string='Training Plan',
        states={
            'active': [('readonly', True)],
            'ended': [('readonly', True)],
            'cancelled': [('readonly', True)],
        },
        ondelete='cascade',
        index=True,
        required=True,
    )
    subject_id = fields.Many2one(
        comodel_name='edu.subject',
        string='Subject',
        states={
            'active': [('readonly', True)],
            'ended': [('readonly', True)],
            'cancelled': [('readonly', True)],
        },
        required=True,
    )
    teacher_id = fields.Many2one(
        comodel_name='res.partner',
        string='Teacher',
        states={
            'active': [('readonly', True)],
            'ended': [('readonly', True)],
            'cancelled': [('readonly', True)],
        },
        domain='[("is_teacher", "=", True)]',
    )
    classroom_id = fields.Many2one(
        comodel_name='edu.training.plan.classroom',
        string='Classroom',
        help='Classrooms must be created from "Classroom" tab.',
        states={
            'active': [('readonly', True)],
            'ended': [('readonly', True)],
            'cancelled': [('readonly', True)],
        },
        required=True,
    )
    student_ids = fields.One2many(
        comodel_name='res.partner',
        compute='_compute_students',
        string='Students',
    )
    student_count = fields.Integer(
        compute='_compute_students',
        string='Enrolled students',
    )
    bulletin_ids = fields.One2many(
        comodel_name='edu.marks.bulletin',
        compute='_compute_bulletins',
        string='Bulletins',
    )
    bulletin_count = fields.Integer(
        compute='_compute_bulletins',
        string='Bulletins count',
    )
    user_id = fields.Many2one(
        comodel_name='res.users',
        string='Responsible',
        domain=[('share', '=', False)],
    )
    start_date = fields.Date(
        string='Start date',
        required=True,
    )
    end_date = fields.Date(
        string='End date',
        required=True,
    )
    schedule = fields.Char(
        string='Schedule',
    )
    estimated_hours = fields.Float(
        string='Estimated hours',
    )
    notes = fields.Text()

    @api.onchange('training_plan_id')
    def onchange_training_plan_id(self):
        if not self.training_plan_id:
            return
        self.start_date = self.training_plan_id.start_date
        self.end_date = self.training_plan_id.end_date

    @api.constrains('start_date', 'end_date')
    def constrains_booking_dates(self):
        if (self.start_date > self.end_date):
            raise exceptions.ValidationError(
                _('Start date date must be equal or before than date end'))

    @api.depends('training_plan_id', 'subject_id', 'teacher_id',
                 'classroom_id')
    def _compute_name(self):
        for line in self:
            data = dict(
                training_plan=line.training_plan_id.short_name or '',
                subject=line.subject_id.short_name or '',
                classroom=line.classroom_id and line.classroom_id.name or '',
                teacher=(
                    line.teacher_id and '(%s)' % line.teacher_id.name or ''))
            line.name = (
                '%(training_plan)s %(subject)s %(classroom)s %(teacher)s' % (
                    data))

    def _compute_students(self):
        enroll_obj = self.env['edu.enrollment']
        for line in self:
            enrollments = enroll_obj.search([
                ('training_plan_id', '=', line.training_plan_id.id),
                ('classroom_id', '=', line.classroom_id.id),
                ('enrollment_line_ids.subject_id', 'in', [line.subject_id.id]),
                ('state', '=', 'active'),
            ])
            student_ids = [enr.student_id.id for enr in enrollments]
            line.student_ids = [(6, 0, student_ids)]
            line.student_count = len(line.student_ids)

    def _compute_bulletins(self):
        for line in self:
            line.bulletin_ids = [(6, 0, self.env['edu.marks.bulletin'].search([
                ('classroom_id', '=', line.classroom_id.id),
                ('evaluation_line_ids.subject_id', 'in', [line.subject_id.id]),
            ]))]
            line.bulletin_count = len(line.bulletin_ids)

    def show_training_plan_enrollments(self):
        self.ensure_one()
        enrollments = self.env['edu.enrollment'].search([
            ('training_plan_id', '=', self.training_plan_id.id),
            ('classroom_id', '=', self.classroom_id.id),
            ('enrollment_line_ids.subject_id', 'in', [self.subject_id.id]),
            ('state', '=', 'active'),
        ])
        action = self.env.ref('education.action_edu_enrollment').read()[0]
        action['domain'] = [('id', 'in', enrollments.ids)]
        return action

    def show_mark_bulletins(self):
        self.ensure_one()
        bulletins = self.env['edu.marks.bulletin'].search([
            ('classroom_id', '=', self.classroom_id.id),
            ('evaluation_line_ids.subject_id', 'in', [self.subject_id.id]),
        ])
        action = self.env.ref('education.action_edu_marks_bulletin').read()[0]
        action['domain'] = [('id', 'in', bulletins.ids)]
        return action

    def to_active(self):
        self.ensure_one()
        if not self.state == 'draft':
            return
        self.state = 'active'

    def to_ended(self):
        self.ensure_one()
        if not self.state == 'active':
            return
        self.state = 'ended'

    def to_cancelled(self):
        self.ensure_one()
        if self.state not in ['draft', 'active']:
            return
        self.state = 'cancelled'

    def to_draft(self):
        self.ensure_one()
        if not self.state == 'cancelled':
            return
        self.state = 'draft'

    def _search_ev_lines(self, ev_lines_domain):
        return self.env['edu.evaluation.line'].search(ev_lines_domain)

    def create_evaluation_lines(self, student, bulletin, evaluation_id):
        for plan_line in self:
            is_shown = plan_line.subject_id.show_in_bulletin
            if plan_line.classroom_id == bulletin.classroom_id and is_shown:
                ev_lines_domain = [
                    ('subject_id', '=', plan_line.subject_id.id),
                    ('evaluation_id', '=', evaluation_id.id),
                    ('student_id', '=', student.id),
                ]
                if not plan_line.subject_id.evaluable_concept_ids:
                    if not self._search_ev_lines(ev_lines_domain):
                        self.env['edu.evaluation.line'].create({
                            'bulletin_id': bulletin.id,
                            'subject_id': plan_line.subject_id.id,
                            'evaluation_id': evaluation_id.id,
                            'student_id': student.id,
                        })
                else:
                    evaluable_concepts = (
                        plan_line.subject_id.evaluable_concept_ids)
                    for evaluable_concept in evaluable_concepts:
                        ev_lines_domain.append(
                            ('concept_id', '=', evaluable_concept.id))
                        if not self._search_ev_lines(ev_lines_domain):
                            self.env['edu.evaluation.line'].create({
                                'bulletin_id': bulletin.id,
                                'subject_id': plan_line.subject_id.id,
                                'evaluation_id': evaluation_id.id,
                                'student_id': student.id,
                                'concept_id': evaluable_concept.id,
                            })
                        ev_lines_domain.remove(
                            ('concept_id', '=', evaluable_concept.id))

    def generate_bulletins(self):
        self.ensure_one()
        view = self.env.ref('education.generate_bulletins_wizard')
        return {
            'model': self.id,
            'res_model': 'edu.wizard.generate.bulletins',
            'target': 'new',
            'type': 'ir.actions.act_window',
            'view_id': view.id,
            'view_mode': 'form',
            'view_type': 'form',
        }
