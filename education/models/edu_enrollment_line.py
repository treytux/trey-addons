# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields, api


class EduEnrollmentLine(models.Model):
    _name = 'edu.enrollment.line'
    _description = 'Enrollment Line'
    _inherit = ['mail.thread']

    name = fields.Char(
        compute='_compute_name',
        string='Name')
    enrollment_id = fields.Many2one(
        comodel_name='edu.enrollment',
        string='Enrollment',
        required=True)
    subject_id = fields.Many2one(
        comodel_name='edu.subject',
        string='Subject',
        required=True)
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
        track_visibility='onchange')

    @api.one
    @api.depends('enrollment_id', 'subject_id')
    def _compute_name(self):
        data = dict(
            enrollment=self.enrollment_id.name or '',
            subject=self.subject_id.short_name or '')
        self.name = (
            '%(enrollment)s %(subject)s' % data)
