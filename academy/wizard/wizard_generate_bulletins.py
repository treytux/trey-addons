###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, api, exceptions, fields, models


class AcademyWizardGenerateBulletins(models.TransientModel):
    _name = 'academy.wizard.generate.bulletin'
    _description = 'Wizard generate bulletin'

    @api.model
    def _get_domain_evaluation_id(self):
        active_model = self.env.context.get('active_model', False)
        active_ids = self.env.context.get('active_ids', False)
        if active_model != 'academy.activity' or not active_ids:
            return False
        activities = self.env[active_model].browse(active_ids)
        return [('id', 'in', activities.mapped('evaluation_ids.id'))]

    evaluation_id = fields.Many2one(
        comodel_name='academy.evaluation',
        string='Evaluation',
        required=True,
        domain=_get_domain_evaluation_id,
    )
    date = fields.Date(
        string='Date',
        required=True,
        default=fields.Date.context_today,
    )

    def button_accept(self):
        self.ensure_one()
        active_model = self.env.context.get('active_model', False)
        active_ids = self.env.context.get('active_ids', False)
        if active_model != 'academy.activity' or not active_ids:
            raise exceptions.UserError(_('Please select one activity.'))
        activities = self.env[active_model].browse(active_ids)
        academy_marks_bulletin_obj = self.env['academy.marks.bulletin']
        for activity in activities:
            if self.evaluation_id not in activity.evaluation_ids:
                continue
            enrollments = activity.enrollment_ids.filtered(
                lambda e: e.state in ['active', 'ended', 'dropout']
                and e.start_date <= self.date
                and (not e.end_date or e.end_date >= self.date)
            )
            for enrollment in enrollments:
                student = enrollment.student_id
                bulletin = self.env['academy.marks.bulletin'].search([
                    ('enrollment_id', '=', enrollment.id),
                ])
                if not bulletin:
                    bulletin = academy_marks_bulletin_obj.create({
                        'name': student.id,
                        'enrollment_id': enrollment.id,
                    })
                bulletin.create_bulletin_lines(self.evaluation_id)
        return {'type': 'ir.actions.act_window_close'}
