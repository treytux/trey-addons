# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields, api, _
from openerp.exceptions import ValidationError


class EduEvaluationLine(models.Model):
    _name = 'edu.evaluation.line'
    _description = 'Evaluation Line'
    _order = 'evaluation_id'

    enrollment_id = fields.Many2one(
        comodel_name='edu.enrollment',
        string='Enrollment',
        required=False)
    subject_id = fields.Many2one(
        comodel_name='edu.subject',
        string='Subject',
        required=True)
    mark = fields.Integer(
        string='Mark',
        default=0,
        size=1)
    evaluation_id = fields.Many2one(
        comodel_name='edu.evaluation',
        string='Evaluation',
        required=False)
    validated = fields.Boolean(
        default=False,
        string='Validated')

    @api.constrains('mark')
    @api.one
    def _check_number(self):
        if self.mark and self.mark > 10:
            raise ValidationError(_('Max value is 10'))
