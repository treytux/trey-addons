###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    rental_allow_products = fields.Boolean(
        string='Allow regular products in rental orders',
        config_parameter='rental_base_extend.rental_allow_products',
    )
