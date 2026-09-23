###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class EduWizardMigrateStudent(models.TransientModel):
    _name = 'edu.wizard.migrate.student'
    _description = 'Wizard Migrate Student'

    tp_origin_id = fields.Many2one(
        comodel_name='edu.training.plan',
        string='Origin Training Plan',
        default=lambda self: self.env.context.get('active_id'),
        required=True,
    )
    tp_dest_id = fields.Many2one(
        comodel_name='edu.training.plan',
        string='Destination Training Plan',
        required=True,
    )
    class_origin_id = fields.Many2one(
        comodel_name='edu.training.plan.classroom',
        string='Origin Classroom',
        required=True,
        domain='[("training_plan_id", "=", tp_origin_id)]',
    )
    class_dest_id = fields.Many2one(
        comodel_name='edu.training.plan.classroom',
        string='Destination Classroom',
        required=True,
        domain='[("training_plan_id", "=", tp_dest_id)]',
    )
    line_ids = fields.One2many(
        comodel_name='edu.wizard.migrate.student.line',
        inverse_name='migrate_id',
        string='Students and Enrollments',
    )

    def button_migrate(self):
        self.ensure_one()
        if not self.tp_dest_id or not self.class_dest_id:
            return
        for line in self.line_ids:
            new_enrollment = line.enrollment_id.copy({
                'training_plan_id': self.tp_dest_id.id,
                'classroom_id': self.class_dest_id.id,
            })
            new_enrollment.fill_subjects()
            line.enrollment_id.to_ended()

    def button_fill_student(self):
        self.ensure_one()
        if not self.tp_origin_id or not self.class_origin_id:
            return
        enrollments = self.env['edu.enrollment'].search([
            ('training_plan_id', '=', self.tp_origin_id.id),
            ('classroom_id', '=', self.class_origin_id.id),
            ('state', '=', 'active'),
        ])
        self.line_ids.create([{
            'migrate_id': self._origin.id,
            'student_id': e.student_id.id,
            'enrollment_id': e.id,
        } for e in enrollments])
        return {
            'context': self.env.context,
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'edu.wizard.migrate.student',
            'res_id': self.id,
            'view_id': False,
            'type': 'ir.actions.act_window',
            'target': 'new',
        }


class WizardMigrateStudentLine(models.TransientModel):
    _name = 'edu.wizard.migrate.student.line'
    _description = 'Wizard Migrate Student Line'

    migrate_id = fields.Many2one(
        comodel_name='edu.wizard.migrate.student',
        string='Migrate ID',
    )
    student_id = fields.Many2one(
        comodel_name='res.partner',
        string='Student',
    )
    enrollment_id = fields.Many2one(
        comodel_name='edu.enrollment',
        string='Enrollment',
    )
