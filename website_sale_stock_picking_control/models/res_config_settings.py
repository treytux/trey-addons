###############################################################################
# For copyright and license notices, see __manifest__.py file
###############################################################################
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    sale_order_skip_stock_picking = fields.Boolean(
        related='website_id.sale_order_skip_stock_picking',
        readonly=False,
    )
