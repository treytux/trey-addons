###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class DeliveryCarrier(models.Model):
    _inherit = 'delivery.carrier'

    team_pricelist_ids = fields.One2many(
        comodel_name='product.team.pricelist',
        inverse_name='carrier_id',
        string='Sales Team Pricelist',
    )
