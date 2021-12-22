###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class Website(models.Model):
    _inherit = 'website'

    token_access = fields.Selection(
        selection=[
            ('all_users', 'All users'),
            ('internal_users', 'Internal users only'),
            ('external_users', 'External users only'),
        ],
        string='Token access',
        help='Indicates which type of users can login with token',
        default='external_users',
    )
