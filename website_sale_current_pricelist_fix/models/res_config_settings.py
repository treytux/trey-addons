###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    default_pricelist_id = fields.Many2one(
        comodel_name='product.pricelist',
        default_model='website',
        related='website_id.default_pricelist_id',
        string='Default pricelist',
        readonly=False,
    )
