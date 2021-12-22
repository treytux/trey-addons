###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class Website(models.Model):
    _inherit = 'website'

    notify_sale = fields.Boolean(
        string='Notify sale',
    )
    notify_done = fields.Boolean(
        string='Notify blocked order',
    )
    notify_cancel = fields.Boolean(
        string='Notify cancel',
    )
