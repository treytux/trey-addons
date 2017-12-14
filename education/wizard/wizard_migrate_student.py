# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import api, models, fields


class EduWizardMigrateStudent(models.TransientModel):
    _name = 'edu.wizard.migrate.student'
    _description = 'Wizard Migrate Student'

    tp_origin_id = fields.Many2one(
        comodel_name='edu.training.plan',
        string='Origin Training Plan',
        default=lambda self: self.env.context.get('active_id'),
        required=True)
    tp_dest_id = fields.Many2one(
        comodel_name='edu.training.plan',
        string='Destination Training Plan',
        required=True)
    class_origin_id = fields.Many2one(
        comodel_name='edu.training.plan.classroom',
        string='Origin Classroom',
        required=True,
        domain="[('training_plan_id','=',tp_origin_id)]")
    class_dest_id = fields.Many2one(
        comodel_name='edu.training.plan.classroom',
        string='Destination Classroom',
        required=True,
        domain="[('training_plan_id','=',tp_dest_id)]")
    line_ids = fields.One2many(
        comodel_name='edu.wizard.migrate.student.line',
        inverse_name='migrate_id',
        string='Students and Enrollments')

    @api.multi
    def button_migrate(self):
        for line in self.line_ids:
            line.enrollment_id.copy({
                'training_plan_id': self.tp_dest_id.id,
                'classroom_id': self.class_dest_id.id})
            line.enrollment_id.to_ended()

    @api.onchange('class_origin_id')
    def _onchange_class_dest_id(self):
        if not self.tp_origin_id or not self.class_origin_id:
            return
        enrollments = self.env['edu.enrollment'].search([
            ('training_plan_id', '=', self.tp_origin_id.id),
            ('classroom_id', '=', self.class_origin_id.id),
            ('state', '=', 'active')])
        self.line_ids = [
            {'student_id': e.student_id.id, 'enrollment_id': e.id}
            for e in enrollments]


class WizardMigrateStudentLine(models.TransientModel):
    _name = 'edu.wizard.migrate.student.line'
    _description = 'Wizard Migrate Student Line'

    migrate_id = fields.Many2one(
        comodel_name='edu.wizard.migrate.student',
        string='Student to Migrate')
    student_id = fields.Many2one(
        comodel_name='res.partner',
        string='Student')
    enrollment_id = fields.Many2one(
        comodel_name='edu.enrollment',
        string='Enrollment')
