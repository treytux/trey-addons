###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class EventProduct(models.Model):
    _inherit = 'event.product'

    address_id = fields.Many2one(
        string='Location',
        comodel_name='res.partner',
        required=True,
    )
