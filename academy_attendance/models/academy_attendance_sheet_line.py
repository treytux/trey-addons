###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class AcademyAtendanceSheetLine(models.Model):
    _name = 'academy.attendance.sheet.line'
    _description = 'Attendance Sheet Line'

    name = fields.Char(
        string='Name',
        default=lambda s: s.env['ir.sequence'].next_by_code(
            'academy.attendance.sheet.line'),
        readonly=True,
        copy=False,
    )
    student_id = fields.Many2one(
        comodel_name='res.partner',
        string='Student',
        required=True,
    )
    academic_training_ids = fields.Many2many(
        related='student_id.academic_training_ids',
        readonly=True,
    )
    main_tutor_id = fields.Many2one(
        comodel_name='res.partner',
        string='Tutor',
        compute='compute_main_tutor_id',
        store=True,
    )
    tutor_mobile = fields.Char(
        related='main_tutor_id.mobile',
        readonly=True,
    )
    present = fields.Boolean(
        string='Present?',
        default=True,
    )
    comments = fields.Char(
        string='Comments',
    )
    attendance_sheet_id = fields.Many2one(
        comodel_name='academy.attendance.sheet',
        string='Attendance Sheet',
    )
    date = fields.Date(
        string='Date',
        related='attendance_sheet_id.date',
        readonly=True,
    )
    activity_id = fields.Many2one(
        comodel_name='academy.activity',
        related='attendance_sheet_id.activity_id',
        readonly=True,
    )

    @api.depends('student_id', 'student_id.tutor_ids')
    def compute_main_tutor_id(self):
        for line in self:
            line.main_tutor_id = False
            if not line.student_id:
                continue
            line.main_tutor_id = (
                line.student_id.tutor_ids and line.student_id.tutor_ids[0].id
                or False)
