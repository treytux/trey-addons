###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class PartnerHistoryType(models.Model):
    _name = 'partner.history.type'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Partner history type'

    name = fields.Char(
        string='Name',
        translate=True,
        required=True,
        tracking=True,
    )
