###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import copy

from odoo import api, models


class EducationEduEnrollment(models.TransientModel):
    _name = 'report.education.edu_enrollment'
    _description = 'Edu enrollment'

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['edu.enrollment'].browse(docids)
        report_obj = self.env['ir.actions.report']
        report = report_obj._get_report_from_name('education.edu_enrollment')
        return {
            'data': data,
            'docs': docs,
            'doc_model': report.model,
        }


class EducationEduMarksBulletin(models.TransientModel):
    _name = 'report.education.edu_marks_bulletin'
    _description = 'Edu Marks Bulletin'

    @api.model
    def get_evaluations_labels(self, evaluation_sequence):
        return self.env['edu.evaluation'].search([
            ('sequence', '<=', evaluation_sequence),
        ], order='sequence')

    @api.model
    def get_mark_keys(self, bulletins, evaluation_sequence):
        min_seq = min(
            bulletins.mapped('evaluation_line_ids.evaluation_id.sequence'))
        return {i: dict(mark=False) for i in range(
            min_seq, evaluation_sequence + 1)}

    @api.model
    def get_marks(self, bulletins, evaluation_sequence):
        mark_keys = self.get_mark_keys(bulletins, evaluation_sequence)
        lines = {}
        for bulletin in bulletins:
            has_concept = any(bulletin.mapped('evaluation_line_ids.concept_id'))
            dic = lines.setdefault(
                bulletin, {
                    'has_concept': has_concept,
                    'lines': {},
                })
            for line in bulletin.evaluation_line_ids:
                if line.evaluation_id.sequence > evaluation_sequence:
                    continue
                marks = dic['lines'].setdefault(
                    line.concept_id or line.subject_id, {
                        'concept': (
                            line.concept_id and line.concept_id.name or ''),
                        'enrollment': line.subject_id.name,
                        'evaluations': copy.deepcopy(mark_keys),
                        'validated': line.validated,
                    })
                marks['evaluations'][
                    line.evaluation_id.sequence]['mark'] = line.mark
        return lines

    @api.model
    def _get_report_values(self, docids, data=None):
        report_obj = self.env['ir.actions.report']
        marks_bulletins_obj = self.env['edu.marks.bulletin']
        report = report_obj._get_report_from_name(
            'education.edu_marks_bulletin')
        docs = marks_bulletins_obj.browse(data['active_ids'])
        evaluation = self.env['edu.evaluation'].browse(data['evaluation_id'])
        enrollments = self.get_marks(docs, evaluation.sequence)
        return {
            'data': data,
            'docs': docs,
            'doc_model': report.model,
            'evaluation': data['evaluation_id'],
            'ev_labels': self.get_evaluations_labels(evaluation.sequence),
            'enrollments': enrollments,
        }
