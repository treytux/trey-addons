###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    website_public_users = fields.Many2many(
        related='website_id.website_public_users',
        relation='res.users',
        string='Website public users',
    )
