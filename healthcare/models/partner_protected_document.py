###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class PartnerProtectedDocument(models.Model):
    _name = 'partner.protected.document'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Partner protected document'

    name = fields.Char(
        string='Name',
        translate=True,
        tracking=True,
    )
    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Partner user',
        required=True,
        tracking=True,
    )
    category_id = fields.Many2one(
        comodel_name='partner.protected.document.category',
        string='Category',
        required=True,
        tracking=True,
    )
    file = fields.Binary(
        string='File',
        tracking=True,
    )
