# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields, api, _
from openerp.exceptions import ValidationError


class EduEvaluationLine(models.Model):
    _name = 'edu.evaluation.line'
    _description = 'Evaluation Line'
    _order = 'evaluation_id, subject_id'

    bulletin_id = fields.Many2one(
        comodel_name='edu.marks.bulletin',
        string='Bulletin')
    subject_id = fields.Many2one(
        comodel_name='edu.subject',
        string='Subject',
        required=True)
    mark = fields.Integer(
        string='Mark',
        default=0)
    evaluation_id = fields.Many2one(
        comodel_name='edu.evaluation',
        string='Evaluation')
    validated = fields.Boolean(
        string='Validated')
    student_id = fields.Many2one(
        comodel_name='res.partner',
        string='Partner')

    @api.constrains('mark')
    @api.one
    def _check_number(self):
        if self.mark and self.mark > 10:
            raise ValidationError(_('Max value is 10'))
