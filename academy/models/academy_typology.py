###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class AcademyTypology(models.Model):
    _name = 'academy.typology'
    _description = 'Typology'
    _inherit = ['mail.thread']

    name = fields.Char(
        string='Name',
        required=True,
    )
    enrollment_conditions = fields.Text(
        string='Enrollment Conditions',
    )
    access_requeriments = fields.Text(
        string='Access Requeriments',
    )
    active = fields.Boolean(
        string='Active',
        default=True,
    )
