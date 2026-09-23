###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, api, exceptions, fields, models


class EduWizardGenerateBulletins(models.TransientModel):
    _name = 'edu.wizard.generate.bulletins'
    _description = 'Wizard generate bulletins'

    evaluation_id = fields.Many2one(
        comodel_name='edu.evaluation',
        string='Evaluation',
    )

    @api.model
    def _search_ev_lines(self, ev_lines_domain):
        return self.env['edu.evaluation.line'].search(ev_lines_domain)

    @api.model
    def _search_bulletins(self, bulletin_domain):
        bulletins = self.env['edu.marks.bulletin'].search(bulletin_domain)
        if len(bulletins) > 1:
            raise exceptions.ValidationError(
                _('There are more than one bulletin for this student '
                  'and enrollment.'))
        return bulletins

    def get_bulletins_data(self, student, enrollment, training_plan_line):
        return {
            'name': student.id,
            'enrollment_id': enrollment.id,
            'training_plan_line_id': training_plan_line.id,
        }

    def get_enrollment_domain(self, training_plan_line):
        return [
            ('classroom_id', '=', training_plan_line.classroom_id.id),
            ('training_plan_id', '=', training_plan_line.training_plan_id.id),
            ('state', 'in', ['active', 'ended', 'dropout']),
        ]

    def button_accept(self):
        self.ensure_one()
        active_model = self.env.context.get('active_model', False)
        active_ids = self.env.context.get('active_ids', False)
        if not active_model or not active_ids:
            raise exceptions.UserError(_('Please select one enrollment.'))
        training_plan_lines = self.env[active_model].browse(active_ids)
        edu_enrollment_obj = self.env['edu.enrollment']
        edu_marks_bulletin_obj = self.env['edu.marks.bulletin']
        for training_plan_line in training_plan_lines:
            training_plan = training_plan_line.training_plan_id
            enrollments = edu_enrollment_obj.search(
                self.get_enrollment_domain(training_plan_line))
            for enrollment in enrollments:
                student = enrollment.student_id
                classroom = training_plan_line.classroom_id
                bulletin = self._search_bulletins([
                    ('name', '=', student.id),
                    ('enrollment_id', '=', enrollment.id),
                ])
                if not bulletin:
                    bulletin = edu_marks_bulletin_obj.create(
                        self.get_bulletins_data(
                            student, enrollment, training_plan_line))
                enrollments = edu_enrollment_obj.search([
                    ('student_id', '=', student.id),
                    ('classroom_id', '=', classroom.id),
                    ('state', '=', 'active'),
                ])
                if len(enrollments) > 1:
                    raise exceptions.ValidationError(
                        _('There are duplicate active enrollments '
                            'for this student: %s') % student.name)
                if not training_plan.line_ids:
                    raise exceptions.ValidationError(
                        _('There are not subjects configured in '
                            'trainign plan: %s') % training_plan.name)
                training_plan.line_ids.create_evaluation_lines(
                    student, bulletin, self.evaluation_id)
        return {'type': 'ir.actions.act_window_close'}
