###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    is_season = fields.Boolean(
        string='Is season',
    )
    sale_order_id = fields.Many2one(
        comodel_name='sale.order',
        string='Sale Order',
    )
