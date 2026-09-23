###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class WizardSetEmployee(models.TransientModel):
    _name = 'wizard.set.employee'
    _description = 'Wizard to set employee'

    related_user = fields.Many2one(
        comodel_name='res.users',
        string='Related User',
    )

    def set_employee(self):
        context = self._context
        employee_obj = self.env['hr.employee'].search([
            ('id', '=', context.get('employee_id')),
        ])
        if self.related_user:
            employee_obj.user_id = self.related_user
        employee_obj.set_as_employee()
