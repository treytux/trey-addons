###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class EduEnrollmentLine(models.Model):
    _name = 'edu.enrollment.line'
    _description = 'Enrollment Line'
    _inherit = ['mail.thread']

    name = fields.Char(
        compute='_compute_name',
        string='Name',
    )
    enrollment_id = fields.Many2one(
        comodel_name='edu.enrollment',
        string='Enrollment',
        required=True,
    )
    subject_id = fields.Many2one(
        comodel_name='edu.subject',
        string='Subject',
        required=True,
    )
    state = fields.Selection(
        selection=[
            ('enrolled', 'Enrolled'),
            ('unenrolled', 'Unenrolled'),
            ('passed', 'Passed'),
            ('validated', 'Validated'),
        ],
        string='State',
        default='enrolled',
        required=True,
        track_visibility='onchange',
    )

    @api.depends('enrollment_id', 'subject_id')
    def _compute_name(self):
        for enr_line in self:
            data = dict(
                enrollment=enr_line.enrollment_id.name or '',
                subject=enr_line.subject_id.short_name or '')
            enr_line.name = ('%(enrollment)s %(subject)s' % data)
