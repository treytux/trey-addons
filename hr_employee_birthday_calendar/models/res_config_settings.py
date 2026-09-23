###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    employee_birthday_notification = fields.Boolean(
        string='Send employee birthday notifications',
        readonly=False,
        config_parameter=(
            'hr_employee_birthday_calendar.employee_birthday_notification',
        ),
    )

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        param_obj = self.env['ir.config_parameter']
        employee_birthday_notification = param_obj.get_param(
            'hr_employee_birthday_calendar.employee_birthday_notification')
        res.update(
            employee_birthday_notification=employee_birthday_notification)
        return res

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        set_param = self.env['ir.config_parameter'].sudo().set_param
        set_param(
            'hr_employee_birthday_calendar.employee_birthday_notification',
            self.employee_birthday_notification)
