###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    location_reserve_default = fields.Many2one(
        comodel_name='stock.location',
        string='Source location to reserve products by default',
        required=True,
    )
