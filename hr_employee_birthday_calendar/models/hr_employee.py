###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, api, fields, models


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    current_birthday = fields.Date(
        string='Birthday',
        compute='_compute_current_birthday',
        search='_search_current_birthday',
        selectable=False,
    )

    def fields_get(self, allfields=None, attributes=None):
        res = super().fields_get(allfields, attributes=attributes)
        birthday_field = res.get('current_birthday', False)
        if birthday_field:
            birthday_field.update({
                'selectable': False,
                'sortable': False,
                'exportable': False,
            })
        return res

    @api.depends('birthday')
    def _compute_current_birthday(self):
        for employee in self:
            now = fields.Datetime.now()
            date = employee.birthday
            if date:
                now = now.replace(day=date.day, month=date.month)
                employee.current_birthday = now.date()

    def _search_current_birthday(self, operator, value):
        employees = self.search([
            ('birthday', '!=', False),
        ])
        if operator == '>=':
            for employee in employees:
                now = fields.Date.to_date(value)
                date = employee.birthday
                if now.month >= 11 and date.month <= 2:
                    now = now.replace(
                        day=date.day, month=date.month, year=now.year + 1)
                else:
                    now = now.replace(day=date.day, month=date.month)
                employee.current_birthday = now
        return [('id', 'in', employees.ids)]

    def cron_send_birthday_notification(self):
        config_param = self.env['ir.config_parameter'].sudo().get_param(
            key='hr_employee_birthday_calendar.employee_birthday_notification')
        if not config_param:
            return
        now = fields.Datetime.now().strftime('-%m-%d')
        employees = self.search([
            ('birthday', '=like', '____%s' % now),
        ])
        if employees:
            body = (_('Today is the birthday of: %s') % (
                ', '.join(employees.mapped('name'))))
            self.env.ref('mail.channel_all_employees').message_post(
                body=body, subtype_xmlid='mail.mt_comment')
