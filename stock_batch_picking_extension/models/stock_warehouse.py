###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models, fields


class StockWarehouse(models.Model):
    _inherit = 'stock.warehouse'

    default_picker_id = fields.Many2one(
        default=lambda s: s.env.user.id,
        domain='[("share", "=", False)]')
