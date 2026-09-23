######################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    task_warn = fields.Selection(
        selection=[
            ('no-message', 'No Message'),
            ('warning', 'Warning'),
            ('block', 'Block'),
        ],
        string='Project Task',
        default='no-message',
    )
    task_warn_msg = fields.Text(
        string='Message for Project Task',
    )
