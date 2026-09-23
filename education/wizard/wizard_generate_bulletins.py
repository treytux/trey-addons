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
            raise exceptions.ValidationError(_(
                'There are more than one bulletin for this student and '
                'enrollment.'))
        return bulletins

    def get_bulletins_data(self, student, enrollment):
        return {
            'name': student.id,
            'enrollment_id': enrollment.id,
        }

    def get_enrollment_domain(self, plan_line):
        return [
            ('training_plan_id', '=', plan_line.training_plan_id.id),
            ('classroom_id', '=', plan_line.classroom_id.id),
            ('enrollment_line_ids.subject_id', 'in', [plan_line.subject_id.id]),
            ('state', '=', 'active'),
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
            enrollments = edu_enrollment_obj.search(
                self.get_enrollment_domain(training_plan_line))
            for enrollment in enrollments:
                student = enrollment.student_id
                bulletin = self._search_bulletins([
                    ('name', '=', student.id),
                    ('enrollment_id', '=', enrollment.id),
                ])
                if not bulletin:
                    bulletin = edu_marks_bulletin_obj.create(
                        self.get_bulletins_data(student, enrollment))
                training_plan_line.create_evaluation_lines(
                    student, bulletin, self.evaluation_id)
        return {'type': 'ir.actions.act_window_close'}
