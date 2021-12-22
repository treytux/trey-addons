###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class Website(models.Model):
    _inherit = 'website'

    notify_stock_confirmed = fields.Boolean(
        string='Notify stock confirmed',
    )
    notify_stock_assigned = fields.Boolean(
        string='Notify stock assigned',
    )
    notify_stock_done = fields.Boolean(
        string='Notify stock done',
    )
    notify_stock_cancel = fields.Boolean(
        string='Notify stock cancel',
    )
