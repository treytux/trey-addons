###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, api, exceptions, fields, models


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    is_activity_selectable = fields.Boolean(
        string='Selectable in Activities',
        default=True,
    )
    academic_training_ids = fields.Many2many(
        comodel_name='academy.academic.training',
        relation='employee2academic_training',
        column1='employee_id',
        column2='academic_training_id',
        string='Academic training',
        domain='[("type", "!=", "student")]',
    )

    def _inverse_work_contact_details(self):
        res = super()._inverse_work_contact_details()
        for employee in self:
            if employee.work_contact_id:
                employee.work_contact_id.sudo().write({
                    'is_teacher': employee.is_activity_selectable,
                    'related_employee_id': employee.id,
                })
        return res

    def action_create_user(self):
        self.ensure_one()
        res = super().action_create_user()
        if self.is_activity_selectable:
            user = self.env.ref('academy.template_teacher_user')
        if user:
            group_ids = [g.id for g in user.groups_id]
            res['context']['default_groups_id'] = group_ids
            res['context']['default_partner_id'] = self.work_contact_id.id
        return res

    @api.constrains('academic_training_ids')
    def _check_employee_academic_training(self):
        for employee in self:
            if any(t.type == 'student' for t in employee.academic_training_ids):
                raise exceptions.ValidationError(
                    _('The selected academic training is no compatible with '
                      'employees.'))
