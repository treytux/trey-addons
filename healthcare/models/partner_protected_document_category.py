###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class PartnerProtectedDocumentCategory(models.Model):
    _name = 'partner.protected.document.category'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Partner protected document category'

    name = fields.Char(
        string='Name',
        translate=True,
        tracking=True,
        required=True,
    )
