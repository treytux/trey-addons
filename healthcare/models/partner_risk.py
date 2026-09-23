###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class PartnerRisk(models.Model):
    _name = 'partner.risk'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Partner risk'

    name = fields.Char(
        string='Name',
        translate=True,
        required=True,
        tracking=True,
    )
