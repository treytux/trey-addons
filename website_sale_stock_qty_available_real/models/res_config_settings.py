###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    website_sale_stock_qty_mode = fields.Selection(
        related='website_id.website_sale_stock_qty_mode',
        readonly=False,
    )
