###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    website_link_ids = fields.One2many(
        comodel_name='res.partner.website.link',
        inverse_name='partner_id',
        string='Website Links'
    )
