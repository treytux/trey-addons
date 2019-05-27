###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    image_slug_path = fields.Char(
        company_dependent=False,
        required=True,
        related='website_id.image_slug_path')
    image_slug_translate = fields.Boolean(
        company_dependent=False,
        related='website_id.image_slug_translate')
