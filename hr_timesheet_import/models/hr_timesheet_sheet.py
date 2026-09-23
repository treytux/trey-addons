###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, api, exceptions, fields, models


class HrTimesheetSheet(models.Model):
    _inherit = 'hr_timesheet.sheet'

    imported_hours = fields.Float(
        string='Imported hours',
    )
    remaining_hours = fields.Float(
        string='Remaining hours to be assigned',
        compute='_compute_remaining_hours',
        store=True,
    )
    sheet_complete = fields.Boolean(
        string='Sheet complete',
    )

    @api.depends('imported_hours', 'timesheet_ids.unit_amount')
    def _compute_remaining_hours(self):
        def convert_to_minutes(time):
            minutes = int(time) * 60
            minutes += round((time - int(time)) * 60)
            return minutes

        for sheet in self:
            if sheet.imported_hours == 0 or not sheet.sheet_complete:
                sheet.remaining_hours = 0
                continue
            line_units = sheet.timesheet_ids.mapped('unit_amount')
            imputed_min = sum([convert_to_minutes(t) for t in line_units])
            diff_min = convert_to_minutes(sheet.imported_hours) - imputed_min
            sheet.remaining_hours = round(diff_min / 60, 2)

    def check_data_keys(self, data):
        key_vals = ['enrollment', 'date', 'incomplete', 'signedhoursamount']
        result = all(key in data for key in key_vals)
        if result is False:
            raise exceptions.ValidationError(_('Missing data for import'))
        return True

    def import_timesheet(self, data):
        self.check_data_keys(data)
        sheet_obj = self.env['hr_timesheet.sheet']
        employees = self.env['hr.employee'].search([
            ('signing_identifier', '=', str(data['enrollment'])),
        ])
        if not employees:
            raise exceptions.ValidationError(
                _('Employee with identifier %s not found') % data['enrollment'])
        employee = employees[0]
        sheet = sheet_obj.search([
            ('employee_id', '=', employee.id),
            ('date_start', '=', data['date']),
            ('date_end', '=', data['date']),
        ])
        if len(sheet) > 1:
            raise exceptions.ValidationError(
                _('More than one timesheet for the same day and employee'))
        if len(sheet) == 1:
            sheet.sheet_complete = True if data['incomplete'] == 'f' else False
            sheet.imported_hours = data['signedhoursamount']
            sheet._compute_remaining_hours()
            msg = (
                'Timesheet updated through the controller on date '
                f'{fields.Datetime.now()}\n<br/>{str(data)}')
            sheet.message_post(body=msg)
            return sheet.id
        sheet = sheet_obj.create({
            'date_end': data['date'],
            'date_start': data['date'],
            'employee_id': employee.id,
            'department_id': employee.department_id.id,
            'sheet_complete': True if data['incomplete'] == 'f' else False,
            'imported_hours': data['signedhoursamount'],
        })
        msg = 'Timesheet imported through the controller on date %s' % (
            fields.Datetime.now())
        sheet.message_post(body=msg)
        return sheet.id
