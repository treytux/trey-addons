###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    supplier_id = fields.Many2one(
        comodel_name='res.partner',
        string='Supplier',
        copy=False,
    )
