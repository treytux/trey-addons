# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import api, models, fields, exceptions, _


class EduWizardFillSubjects(models.TransientModel):
    _name = 'edu.wizard.fill.subjects'
    _description = 'Wizard Fill Subjects'

    evaluation_id = fields.Many2one(
        comodel_name='edu.evaluation',
        string='Evaluation')

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

    @api.model
    def create_evaluation_lines(self, student, training_plan, bulletin):
        if not training_plan.line_ids:
            raise exceptions.ValidationError(
                _('There are not subjects configured in '
                  'trainign plan: %s') % training_plan.name)
        for plan_line in training_plan.line_ids:
            is_shown = plan_line.subject_id.show_in_bulletin
            if plan_line.classroom_id == bulletin.classroom_id and is_shown:
                ev_lines_domain = [
                    ('subject_id', '=', plan_line.subject_id.id),
                    ('evaluation_id', '=', self.evaluation_id.id),
                    ('student_id', '=', student.id)]
                if not self._search_ev_lines(ev_lines_domain):
                    self.env['edu.evaluation.line'].create({
                        'bulletin_id': bulletin.id,
                        'subject_id': plan_line.subject_id.id,
                        'evaluation_id': self.evaluation_id.id,
                        'student_id': student.id})

    @api.multi
    def button_accept(self):
        classroom = self.env['edu.training.plan.classroom'].browse(
            self.env.context['active_id'])
        training_plan = classroom.training_plan_id
        for student in classroom.student_ids:
            enrollments = self.env['edu.enrollment'].search([
                ('student_id', '=', student.id),
                ('training_plan_id', '=', classroom.training_plan_id.id),
                ('state', '=', 'active')])
            if len(enrollments) > 1:
                raise exceptions.ValidationError(
                    _('There are duplicate active enrollments '
                      'for this student: %s') % self.student_id.name)
            bulletin_domain = [
                ('enrollment_id', '=', enrollments.id),
                ('classroom_id', '=', classroom.id)]
            bulletin = self._search_bulletins(bulletin_domain)
            if not bulletin:
                bulletin = self.env['edu.marks.bulletin'].create({
                    'name': student.id,
                    'classroom_id': classroom.id,
                    'enrollment_id': enrollments.id})
            self.create_evaluation_lines(student, training_plan, bulletin)
        return {'type': 'ir.actions.act_window_close'}
