###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class Website(models.Model):
    _inherit = 'website'

    limit_agreements = fields.Integer(
        string='Maximum number of agreements to show',
        default=3,
    )
