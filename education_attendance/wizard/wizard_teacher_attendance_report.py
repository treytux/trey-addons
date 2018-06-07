# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import api, models, fields, _


class EduWizarTeacherdAttendanceReport(models.TransientModel):
    _name = 'edu.wizard.teacher.attendance.report'
    _description = 'Wizard Teacher Attendance Report'

    teacher_id = fields.Many2one(
        comodel_name='res.partner',
        string='Teacher',
        domain=[('is_teacher', '=', True)],
        required=True)
    date_start = fields.Date(
        string='Date Start',
        required=True)
    date_end = fields.Date(
        string='Date End',
        required=True)
    line_ids = fields.One2many(
        comodel_name='edu.wizard.teacher.attendance.report.line',
        inverse_name='wizard_id',
        string='Lines')
    total_minutes = fields.Float(
        string='Total Minutes',
        digits=(5, 2))
    total_hours = fields.Float(
        string='Total Hours',
        digits=(5, 2))
    total_classes = fields.Integer(
        string='Total Classes')
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
        default=lambda self: self.env.user.company_id)

    @api.multi
    def _get_lines(self):
        attendance_ids = self.env['edu.attendance.sheet'].search([
            '|',
            ('teacher_id', '=', self.teacher_id.id),
            '&',
            ('substitution', '=', True),
            ('substitute_teacher_id', '=', self.teacher_id.id),
            ('date', '>=', self.date_start),
            ('date', '<=', self.date_end),
            ('state', '=', 'ended')])
        line_data = [(0, 0, {
            'attendance_sheet_id': att.id}) for att in attendance_ids]
        return line_data

    @api.multi
    def _clear_data(self):
        self.line_ids = []
        self.total_minutes = False
        self.total_hours = False

    @api.onchange('teacher_id', 'date_start', 'date_end')
    def onchange_wizard_data(self):
        if not self.teacher_id or not self.date_start or not self.date_end:
            self._clear_data()
            return
        if self.date_start > self.date_end:
            self.date_start = False
            self.date_end = False
            self.line_ids = []
            return {'warning': {
                'title': _('Invalid dates'),
                'message': _('Date start must be lower than date end.')}}
        line_data = self._get_lines()
        self.line_ids = line_data
        self.total_classes = len(line_data)
        total_duration = round(sum(l.duration for l in self.line_ids), 2)
        self.total_minutes = total_duration
        self.total_hours = total_duration / 60

    @api.multi
    def button_print(self):
        datas = {'ids': [self.id]}
        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'education_attendance.wizard_teacher_attendance',
            'datas': datas,
            'context': {'report_name':
                        'education_attendance.wizard_teacher_attendance'}}


class EduWizarTeacherdAttendanceReportLine(models.TransientModel):
    _name = 'edu.wizard.teacher.attendance.report.line'
    _description = 'Wizard Teacher Attendance Report'

    wizard_id = fields.Many2one(
        comodel_name='edu.wizard.teacher.attendance.report',
        string='Wizard',
        readonly=True)
    attendance_sheet_id = fields.Many2one(
        comodel_name='edu.attendance.sheet',
        string='Attendance Sheet',
        readonly=True)
    substitution = fields.Boolean(
        string='Substitution',
        related='attendance_sheet_id.substitution',
        readonly=True)
    date = fields.Date(
        string='Date',
        related='attendance_sheet_id.date',
        readonly=True)
    training_plan_id = fields.Many2one(
        comodel_name='edu.training.plan',
        string='Training Plan',
        related='attendance_sheet_id.training_plan_line_id.training_plan_id',
        readonly=True)
    classroom_id = fields.Many2one(
        comodel_name='edu.training.plan.classroom',
        string='Classroom',
        related='attendance_sheet_id.training_plan_line_id.classroom_id',
        readonly=True)
    subject_id = fields.Many2one(
        comodel_name='edu.subject',
        string='Subject',
        related='attendance_sheet_id.training_plan_line_id.subject_id',
        readonly=True)
    duration = fields.Integer(
        string='Duration',
        digits=(5, 2),
        related='attendance_sheet_id.duration',
        readonly=True)
