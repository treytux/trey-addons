###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class ResPartnerWebsiteLink(models.Model):
    _name = "res.partner.website.link"
    _description = "Partner Website"

    name = fields.Char(
        string="Name",
        required=True,
    )
    url = fields.Char(
        string="URL",
        required=True,
    )
    user = fields.Char(
        string="User",
    )
    password = fields.Char(
        string="Password",
    )
    is_public = fields.Boolean(
        string="Is public",
    )
    partner_id = fields.Many2one(
        comodel_name="res.partner",
        string="Partner",
        readonly=True,
    )
