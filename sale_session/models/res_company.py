###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    show_confirm_current_session_button = fields.Boolean(
        string='Show confirm with current session button',
        help='Allow to recover sales to current sessions to be done',
        default=True,
    )
