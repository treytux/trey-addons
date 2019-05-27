###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models, fields


class Website(models.Model):
    _inherit = 'website'

    sale_inactive_days = fields.Integer(
        string='Sale Inactive Days',
        default=90)
