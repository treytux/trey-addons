###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class PosOrder(models.Model):
    _inherit = 'pos.order'

    sale_id = fields.Many2one(
        comodel_name='sale.order',
        string='Sale order associated',
    )
