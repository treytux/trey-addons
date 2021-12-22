##############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
##############################################################################
from odoo import fields, models


class Message(models.Model):
    _inherit = 'mail.message'

    is_reminder = fields.Boolean(
        default=False,
        string='Is notified by mail',
    )
