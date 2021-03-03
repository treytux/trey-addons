###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    company_brand = fields.Char(
        string='Company Brand',
        related='website_id.company_brand',
    )
    id_prefix = fields.Char(
        string='Product ID prefix',
        related='website_id.id_prefix',
    )
