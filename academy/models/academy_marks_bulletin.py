###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import Command, _, api, exceptions, fields, models


class AcademyMarksBulletin(models.Model):
    _name = 'academy.marks.bulletin'
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
        default=lambda self: self.env.company,
    )
    enrollment_id = fields.Many2one(
        comodel_name='academy.enrollment',
        string='Enrollment',
        required=True,
        domain='[(\'student_id\',\'=\',name),(\'state\',\'=\',\'active\'),]',
    )
    activity_id = fields.Many2one(
        comodel_name='academy.activity',
        string='Activity',
        related='enrollment_id.activity_id',
    )
    training_plan_id = fields.Many2one(
        comodel_name='academy.training.plan',
        related='enrollment_id.training_plan_id',
    )
    year = fields.Char(
        string='Session',
        compute='_compute_year',
    )
    tutor_ids = fields.Many2many(
        comodel_name='res.partner',
        relation='academy_marks_bulletin2res_partner_rel',
        string='Tutors',
        column1='bulletin_id',
        column2='partner_id',
        compute='_compute_tutors',
    )
    bulletin_line_ids = fields.One2many(
        comodel_name='academy.marks.bulletin.line',
        inverse_name='bulletin_id',
        string='Bulletin Lines',
    )
    promote = fields.Selection(
        selection=[
            ('promote', 'Promote'),
            ('not_promote', 'Not promote'),
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

    @api.constrains('enrollment_id', 'name')
    def _check_duplicated_bulletins(self):
        for bulletin in self:
            records = bulletin.search([
                ('id', '!=', bulletin.id),
                ('enrollment_id', '=', bulletin.enrollment_id.id),
            ])
            if not records:
                continue
            raise exceptions.ValidationError(_(
                'There can only be a bulletin for the '
                'same enrollment \'%s\'.') % (
                    bulletin.enrollment_id.name))

    @api.constrains('enrollment_id', 'name')
    def _check_valid_student_enrollment(self):
        for bulletin in self:
            if bulletin.enrollment_id in bulletin.name.enrollment_ids:
                continue
            raise exceptions.ValidationError(_(
                'The selected enrollment "%s" does not belong to the selected '
                'student "%s".') % (
                    bulletin.enrollment_id.name, bulletin.name.name))

    @api.onchange('name')
    def _onchange_name(self):
        self.enrollment_id = False
        enrollments = self.env['academy.enrollment'].search([
            ('student_id', '=', self.name.id),
            ('state', '=', 'active'),
        ])
        bulletins = self.search([
            ('name', '=', self.name.id),
            ('id', '!=', self._origin.id),
        ])
        enrollments = enrollments.filtered(
            lambda e: e not in bulletins.enrollment_id)[:1]
        if enrollments:
            self.enrollment_id = enrollments

    @api.depends('bulletin_line_ids.eval_concept_mark_id')
    def _compute_has_pending_evaluation(self):
        for bulletin in self:
            bulletin.has_pending_evaluation = any([
                not line.eval_concept_mark_id
                for line in bulletin.bulletin_line_ids])

    @api.depends('enrollment_id')
    def _compute_year(self):
        for bulletin in self:
            training = bulletin.enrollment_id.training_plan_id
            if training and training.start_date and training.end_date:
                bulletin.year = (
                    training.start_date.strftime('%Y')
                    + '-'
                    + training.end_date.strftime('%Y'))
            else:
                bulletin.year = False

    @api.depends('enrollment_id')
    def _compute_tutors(self):
        for bulletin in self:
            bulletin.tutor_ids = [
                Command.set(bulletin.enrollment_id.tutor_ids.ids),
            ]

    def button_fill_evaluations(self):
        self.ensure_one()
        view = self.env.ref('academy.fill_bulletin_line_wizard')
        return {
            'res_model': 'academy.wizard.fill.bulletin.line',
            'target': 'new',
            'type': 'ir.actions.act_window',
            'view_id': view.id,
            'view_mode': 'form',
            'view_type': 'form',
        }

    def _search_bulletin_lines(self, domain):
        return self.env['academy.marks.bulletin.line'].search(domain)

    def create_bulletin_lines(self, evaluation_id):
        for bulletin in self:
            for evaluable_concept in bulletin.activity_id.evaluable_concept_ids:
                domain = [
                    ('bulletin_id', '=', bulletin.id),
                    ('evaluation_id', '=', evaluation_id.id),
                    ('evaluable_concept_id', '=', evaluable_concept.id),
                ]
                if not self._search_bulletin_lines(domain):
                    self.env['academy.marks.bulletin.line'].create({
                        'bulletin_id': bulletin.id,
                        'evaluation_id': evaluation_id.id,
                        'student_id': bulletin.name.id,
                        'evaluable_concept_id': evaluable_concept.id,
                    })
