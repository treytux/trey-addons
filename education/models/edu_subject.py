###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class EduSubject(models.Model):
    _name = 'edu.subject'
    _description = 'Subject'
    _inherit = ['mail.thread']

    name = fields.Char(
        string='Name',
        required=True,
    )
    short_name = fields.Char(
        string='Short name',
    )
    description = fields.Text(
        string='Description',
    )
    active = fields.Boolean(
        string='Active',
        default=True,
    )
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.company,
    )
    show_in_bulletin = fields.Boolean(
        string='Show in bulletins',
        default=True,
    )
    evaluable_concept_ids = fields.Many2many(
        comodel_name='edu.concept',
        relation='subject2edu_concept_rel',
        column1='subject_id',
        column2='concept_id',
        string='Evaluable concepts',
    )
