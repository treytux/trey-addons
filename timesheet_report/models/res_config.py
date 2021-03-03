# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import api, exceptions, models, fields, _

params = [
    ('working_hours', 'timesheet_report.working_hours'),
    ('entrance', 'timesheet_report.entrance'),
    ('break_time', 'timesheet_report.break'),
    ('break_duration', 'timesheet_report.break_duration'),
    ('late_shift', 'timesheet_report.late_shift'),
    ('exit_time', 'timesheet_report.exit_time'),
]


class hr_config_settings(models.TransientModel):
    _inherit = 'hr.config.settings'

    entrance = fields.Float(
        string='Check in time',
        required=True,
    )

    exit_time = fields.Float(
        string='Check out time',
        required=True,
    )

    working_hours = fields.Float(
        string='Working hours',
        required=True,
    )

    break_time = fields.Float(
        string='Break time start',
        required=True,
    )

    break_duration = fields.Integer(
        help='Break time duration in minutes',
        required=True,
        string='Break time duration',
    )

    late_shift = fields.Float(
        required=True,
        string='Late shift check in',
    )

    @api.multi
    @api.constrains('break_duration')
    def _check_break_duration(self):
        self.ensure_one()
        if self.break_duration < 0 or self.working_hours > 120:
            raise exceptions.Warning(
                _('Invalid value in Break time duration, must be 0-120'))

    @api.multi
    @api.constrains('working_hours')
    def _check_working_hours(self):
        self.ensure_one()
        if self.working_hours < 0 or self.working_hours > 23.99:
            raise exceptions.Warning(
                _('Invalid value in Working hours, must be 0,00-23,59'))

    @api.multi
    @api.constrains('exit_time', 'entrance')
    def _check_entrance_exit(self):
        self.ensure_one()
        if self.entrance < 0 or self.entrance > 23.99:
            raise exceptions.Warning(
                _('Check in time invalid, must be 0:00-23:59'))
        if self.exit_time < 0 or self.exit_time > 23.99:
            raise exceptions.Warning(
                _('Check out time Invalid, must be 0:00-23:59'))
        if self.exit_time <= self.entrance:
            raise exceptions.Warning(
                _('Check out time must be higher than check in'))

    @api.multi
    @api.constrains('break_time')
    def _check_break_time(self):
        self.ensure_one()
        if self.break_time < 0 or self.break_time > 23.99:
            raise exceptions.Warning(
                _('Break time invalid, must be 0:00-23:59'))
        if self.break_time < self.entrance or self.break_time > self.exit_time:
            raise exceptions.Warning(
                _('Break time must be inside journey'))

    @api.multi
    @api.constrains('late_shift')
    def _check_late_shift(self):
        self.ensure_one()
        if self.late_shift < 0 or self.late_shift > 23.99:
            raise exceptions.Warning(
                _('Late shift check in invalid, must be 0:00-23:59'))
        if (self.late_shift > self.entrance and
                self.late_shift < self.exit_time):
            raise exceptions.Warning(
                _('Late shift check in should not be inside journey'))

    @api.multi
    def set_params(self):
        self.ensure_one()
        for field_name, key_name in params:
            value = getattr(self, field_name)
            self.env['ir.config_parameter'].set_param(key_name, value)

    @api.model
    def default_get(self, fields):
        res = super(hr_config_settings, self).default_get(fields)
        for field_name, key_name in params:
            val = self.env['ir.config_parameter'].get_param(key_name)
            if not val:
                continue
            res[field_name] = eval(val)
        return res
