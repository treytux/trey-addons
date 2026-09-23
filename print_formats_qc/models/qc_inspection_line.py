###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class QcInspectionLine(models.Model):
    _inherit = 'qc.inspection.line'

    display_type = fields.Selection(
        selection=[
            ('line_section', 'Section'),
            ('line_note', 'Note'),
        ],
        help="Technical field for UX purpose.",
    )
