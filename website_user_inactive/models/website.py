###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models, fields


class Website(models.Model):
    _inherit = 'website'

    user_inactive_days = fields.Integer(
        string='User Inactive Days',
        required=True,
        default=90)
