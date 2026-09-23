###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class EduEvaluationLine(models.Model):
    _name = 'edu.evaluation.line'
    _description = 'Evaluation Line'
    _order = 'evaluation_id, subject_id'

    bulletin_id = fields.Many2one(
        comodel_name='edu.marks.bulletin',
        string='Bulletin',
        ondelete='cascade',
    )
    subject_id = fields.Many2one(
        comodel_name='edu.subject',
        string='Subject',
        required=True,
    )
    concept_id = fields.Many2one(
        comodel_name='edu.concept',
        string='Concept',
    )
    mark = fields.Char(
        string='Mark',
    )
    evaluation_id = fields.Many2one(
        comodel_name='edu.evaluation',
        string='Evaluation',
    )
    validated = fields.Boolean(
        string='Validated',
    )
    student_id = fields.Many2one(
        comodel_name='res.partner',
        string='Partner',
    )
    value_type = fields.Selection(
        related='concept_id.value_type',
    )

    @api.constrains('mark')
    def _check_number(self):
        values_valid = self.concept_id.values_valid
        if not self.mark or not self.value_type:
            return
        if self.value_type == 'numeric':
            mark_int = int(self.mark)
            if mark_int > 0 and mark_int < 10:
                return
            raise ValidationError(_('Mark should be a number between 0 and 10'))
        if self.mark not in values_valid:
            raise ValidationError(_('Mark should be one of %s') % values_valid)

    def write(self, vals):
        for line in self:
            if vals.get('mark') and line.bulletin_id:
                line.bulletin_id.message_post(
                    body=_('Mark changed %s: %s: %s %s -> %s') % (
                        line.subject_id.name, line.concept_id.name,
                        line.evaluation_id.name, line.mark, vals['mark']))
        return super().write(vals)
