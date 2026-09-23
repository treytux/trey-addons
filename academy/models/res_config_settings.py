###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    check_student_limits = fields.Boolean(
        string='Check student limits',
        help='Prevent enrollments when the activity student limit is reached.',
        related='company_id.check_student_limits',
        readonly=False,
    )
