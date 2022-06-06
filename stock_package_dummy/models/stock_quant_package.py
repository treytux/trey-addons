###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class StockQuantPackage(models.Model):
    _inherit = 'stock.quant.package'

    dummy_id = fields.Many2one(
        comodel_name='stock.quant.package_dummy',
        string='Dummy label',
    )
