###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class Website(models.Model):
    _inherit = 'website'

    limit_account = fields.Integer(
        string='Maximum number of invoices to show',
        default=3,
    )
