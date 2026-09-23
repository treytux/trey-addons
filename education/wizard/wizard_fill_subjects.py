###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, exceptions, fields, models


class EduWizardFillSubjects(models.TransientModel):
    _name = 'edu.wizard.fill.subjects'
    _description = 'Wizard Fill Subjects'

    evaluation_id = fields.Many2one(
        comodel_name='edu.evaluation',
        string='Evaluation',
    )

    def _search_bulletins(self, bulletin_domain):
        bulletins = self.env['edu.marks.bulletin'].search(bulletin_domain)
        if len(bulletins) > 1:
            raise exceptions.ValidationError(
                _('There are more than one bulletin for this student '
                  'and enrollment.'))
        return bulletins

    def button_accept(self):
        self.ensure_one()
        bulletin = self.env['edu.marks.bulletin'].browse(
            self.env.context['active_id'])
        classroom = bulletin.classroom_id
        training_plan = bulletin.enrollment_id.training_plan_id
        student = bulletin.name
        enrollments = self.env['edu.enrollment'].search([
            ('student_id', '=', student.id),
            ('classroom_id', '=', classroom.id),
            ('state', '=', 'active'),
        ])
        if len(enrollments) > 1:
            raise exceptions.ValidationError(
                _('There are duplicate active enrollments '
                  'for this student: %s') % student.name)
        if not enrollments:
            raise exceptions.ValidationError(
                _('There are not active enrollments for this student: %s') % (
                    student.name))
        bulletin_domain = [
            ('name', '=', student.id),
            ('enrollment_id', '=', enrollments.id),
        ]
        bulletin = self._search_bulletins(bulletin_domain)
        if not bulletin:
            raise exceptions.ValidationError(
                _('There are not bulletins for this student: %s') % (
                    student.name))
        if not training_plan.line_ids:
            raise exceptions.ValidationError(
                _('There are not subjects configured in '
                  'trainign plan: %s') % training_plan.name)
        training_plan.line_ids.create_evaluation_lines(
            student, bulletin, self.evaluation_id)
        return {'type': 'ir.actions.act_window_close'}
