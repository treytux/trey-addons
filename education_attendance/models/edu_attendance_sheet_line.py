# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields


class EduAtendanceSheetLine(models.Model):
    _name = 'edu.attendance.sheet.line'

    student_id = fields.Many2one(
        comodel_name='res.partner',
        string='Student',
        required=True)
    present = fields.Boolean(
        string='Present?',
        default=True)
    comments = fields.Char(
        string='Comments')
    attendance_sheet_id = fields.Many2one(
        comodel_name='edu.attendance.sheet',
        string='Attendance Sheet')
    date = fields.Date(
        string='Date',
        related='attendance_sheet_id.date',
        readonly=True)
    training_plan_line_id = fields.Many2one(
        comodel_name='edu.training.plan.line',
        related='attendance_sheet_id.training_plan_line_id',
        readonly=True)
