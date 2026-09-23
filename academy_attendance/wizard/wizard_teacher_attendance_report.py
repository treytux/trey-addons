###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, api, fields, models


class AcademyWizarTeacherdAttendanceReport(models.TransientModel):
    _name = 'academy.wizard.teacher.attendance.report'
    _description = 'Wizard Teacher Attendance Report'

    teacher_id = fields.Many2one(
        comodel_name='hr.employee',
        string='Teacher',
        domain=[
            ('is_activity_selectable', '=', True),
        ],
        required=True,
    )
    date_start = fields.Date(
        string='Date Start',
        required=True,
    )
    date_end = fields.Date(
        string='Date End',
        required=True,
    )
    line_ids = fields.One2many(
        comodel_name='academy.wizard.teacher.attendance.report.line',
        inverse_name='wizard_id',
        string='Lines',
    )
    total_minutes = fields.Float(
        string='Total Minutes',
        digits=(5, 2),
    )
    total_hours = fields.Float(
        string='Total Hours',
        digits=(5, 2),
    )
    total_classes = fields.Integer(
        string='Total classes',
    )
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
        default=lambda self: self.env.company,
    )

    def _get_lines(self):
        attendance_ids = self.env['academy.attendance.sheet'].search([
            '|',
            ('teacher_id', '=', self.teacher_id.id),
            '&',
            ('substitution', '=', True),
            ('substitute_teacher_id', '=', self.teacher_id.id),
            ('date', '>=', self.date_start),
            ('date', '<=', self.date_end),
            ('state', '=', 'ended'),
        ])
        line_data = [(0, 0, {
            'attendance_sheet_id': att.id}) for att in attendance_ids]
        return line_data

    def _clear_data(self):
        self.line_ids = [(2, line.id, 0) for line in self.line_ids]
        self.total_minutes = False
        self.total_hours = False

    @api.onchange('teacher_id', 'date_start', 'date_end')
    def onchange_wizard_data(self):
        if not self.teacher_id or not self.date_start or not self.date_end:
            return
        self._clear_data()
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
        total_duration = round(sum(line.duration for line in self.line_ids), 2)
        self.total_minutes = total_duration
        self.total_hours = total_duration / 60

    def get_report_formats(self):
        report_ids = self.env['ir.actions.report'].search([])
        return self.env['ir.actions.report'].browse(report_ids)

    def button_print(self):
        self.ensure_one()
        self.onchange_wizard_data()
        report = 'academy_attendance.academy_teacher_attendance_report_create'
        return self.env.ref(report).report_action(self)


class AcademyWizarTeacherdAttendanceReportLine(models.TransientModel):
    _name = 'academy.wizard.teacher.attendance.report.line'
    _description = 'Wizard Teacher Attendance Report'

    wizard_id = fields.Many2one(
        comodel_name='academy.wizard.teacher.attendance.report',
        string='Wizard',
        readonly=True,
    )
    attendance_sheet_id = fields.Many2one(
        comodel_name='academy.attendance.sheet',
        string='Attendance Sheet',
        readonly=True,
    )
    substitution = fields.Boolean(
        string='Substitution',
        related='attendance_sheet_id.substitution',
        readonly=True,
    )
    date = fields.Date(
        string='Date',
        related='attendance_sheet_id.date',
        readonly=True,
    )
    training_plan_id = fields.Many2one(
        comodel_name='academy.training.plan',
        string='Training Plan',
        related='attendance_sheet_id.activity_id.training_plan_id',
        readonly=True,
    )
    activity_id = fields.Many2one(
        comodel_name='academy.activity',
        string='Activity',
        related='attendance_sheet_id.activity_id',
        readonly=True,
    )
    duration = fields.Float(
        string='Duration',
        digits=(5, 2),
        related='attendance_sheet_id.duration',
        readonly=True,
    )
