###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, fields, models


class AcademyMarksBulletinLine(models.Model):
    _name = 'academy.marks.bulletin.line'
    _description = 'Bulletin Line'
    _order = 'evaluation_id, activity_id'

    bulletin_id = fields.Many2one(
        comodel_name='academy.marks.bulletin',
        string='Bulletin',
        required=True,
        ondelete='cascade',
    )
    activity_id = fields.Many2one(
        comodel_name='academy.activity',
        string='Activity',
        related='bulletin_id.activity_id',
        store=True,
    )
    evaluable_concept_id = fields.Many2one(
        comodel_name='academy.evaluable.concept',
        string='Evaluable concept',
        domain='[(\'activity_ids\', \'in\', [activity_id])]',
    )
    eval_concept_mark_id = fields.Many2one(
        comodel_name='academy.evaluable.concept.mark',
        string='Evaluable concept mark',
        domain='[(\'evaluable_concept_ids\', \'in\', [evaluable_concept_id])]',
    )
    evaluation_id = fields.Many2one(
        comodel_name='academy.evaluation',
        string='Evaluation',
    )
    student_id = fields.Many2one(
        comodel_name='res.partner',
        string='Partner',
    )
    portal_published = fields.Boolean(
        string='Visible on portal',
    )

    def write(self, vals):
        for line in self:
            if vals.get('eval_concept_mark_id'):
                new_mark = self.env['academy.evaluable.concept.mark'].browse(
                    vals['eval_concept_mark_id'])
                line.bulletin_id.message_post(
                    body=_('Mark changed for %s. Evaluation: %s. '
                           'Concept: %s. Mark: %s -> %s') % (
                        line.activity_id.name, line.evaluation_id.name,
                        line.evaluable_concept_id.name,
                        line.eval_concept_mark_id.name or 'No mark',
                        new_mark.name))
        return super().write(vals)
