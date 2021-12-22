###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class Website(models.Model):
    _inherit = 'website'

    notify_invoice_open = fields.Boolean(
        string='Notify open invoice',
    )
    notify_invoice_paid = fields.Boolean(
        string='Notify paid invoice',
    )
