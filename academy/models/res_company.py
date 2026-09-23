###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    check_student_limits = fields.Boolean(
        string='Check student limits',
        help='Prevent enrollments when the activity student limit is reached.',
        default=True,
    )
