###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    default_carrier_id = fields.Many2one(
        comodel_name='delivery.carrier',
        string='Default carrier',
    )
