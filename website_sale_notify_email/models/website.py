###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class Website(models.Model):
    _inherit = 'website'

    notify_new_sale = fields.Boolean()
    notification_type = fields.Selection(
        selection=[
            ('email', 'Email'),
        ],
        default='email',
    )
